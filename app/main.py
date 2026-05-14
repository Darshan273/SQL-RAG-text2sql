import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.db.connection import async_session_factory, dispose_engine
from app.graph.builder import graph
from app.graph.state import AgentState, default_agent_state
from app.schemas.api_models import ErrorResponse, QueryRequest, QueryResponse, ToolInfo
from app.schemas.tool_definitions import TOOL_DEFINITIONS


logger = logging.getLogger("text_to_sql.api")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.settings = settings
    logger.info(
        json.dumps(
            {
                "event": "startup",
                "langsmith_tracing": settings.langsmith_tracing,
                "langsmith_project": settings.langsmith_project,
            },
            ensure_ascii=False,
        )
    )

    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.error(
            json.dumps(
                {
                    "event": "startup_database_check_failed",
                    "detail": str(exc),
                },
                ensure_ascii=False,
            )
        )
        raise RuntimeError(
            "Database startup check failed. Verify DATABASE_URL in .env uses "
            "your real PostgreSQL username, password, host, port, and database."
        ) from exc

    yield

    await dispose_engine()


app = FastAPI(
    title="Text-to-SQL API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _initial_state(question: str) -> AgentState:
    return default_agent_state(question)


def _error_response(status_code: int, error: str, detail: str) -> JSONResponse:
    payload = ErrorResponse(error=error, detail=detail)
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def _safe_question_from_body(body: bytes) -> str:
    if not body:
        return ""

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return ""

    question = payload.get("question", "")
    return question if isinstance(question, str) else ""


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next: Any) -> JSONResponse:
    start_time = time.perf_counter()
    body = await request.body()
    question = _safe_question_from_body(body) if request.url.path == "/query" else ""

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": body, "more_body": False}

    request = Request(request.scope, receive)
    request.state.question = question
    request.state.tool_used = ""
    request.state.sql_generated = ""
    request.state.readonly_violation = False

    response = await call_next(request)

    execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
    if request.url.path == "/query":
        logger.info(
            json.dumps(
                {
                    "event": "query_request",
                    "question": request.state.question,
                    "tool_used": request.state.tool_used,
                    "sql_generated": request.state.sql_generated,
                    "readonly_violation": request.state.readonly_violation,
                    "execution_time_ms": execution_time_ms,
                },
                ensure_ascii=False,
            )
        )

    return response


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return _error_response(422, "Validation error", str(exc))


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError) -> JSONResponse:
    return _error_response(500, "Runtime error", str(exc))


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled application error")
    return _error_response(500, "Internal server error", "An unexpected error occurred.")


@app.post(
    "/query",
    response_model=QueryResponse,
    responses={403: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def query_database(payload: QueryRequest, request: Request) -> QueryResponse | JSONResponse:
    try:
        final_state = await graph.ainvoke(_initial_state(payload.question))
    except Exception as exc:
        logger.exception("Graph execution failed")
        return _error_response(500, "Graph execution failed", str(exc))

    request.state.tool_used = final_state.get("tool_name", "")
    request.state.sql_generated = final_state.get("generated_sql", "")
    request.state.readonly_violation = final_state.get("is_readonly_violation", False)

    if final_state.get("is_readonly_violation", False):
        return _error_response(
            403,
            "Read-only violation",
            final_state.get("error", ""),
        )

    if final_state.get("error"):
        return _error_response(
            500,
            "Query execution failed",
            final_state["error"],
        )

    row_count = len(final_state.get("rows", []))
    total_count = final_state.get("total_count", row_count)

    return QueryResponse(
        answer=final_state.get("answer", ""),
        sql=final_state.get("generated_sql", ""),
        tool_used=final_state.get("tool_name", ""),
        row_count=row_count,
        total_count=total_count,
        readonly_violation=final_state.get("is_readonly_violation", False),
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "model": settings.groq_model,
        "framework": "langgraph",
        "langsmith_tracing": str(settings.langsmith_tracing).lower(),
        "langsmith_project": settings.langsmith_project,
    }


@app.get("/tools", response_model=list[ToolInfo])
async def list_tools() -> list[ToolInfo]:
    return [
        ToolInfo(
            name=tool_definition["function"]["name"],
            description=tool_definition["function"]["description"],
        )
        for tool_definition in TOOL_DEFINITIONS
    ]
