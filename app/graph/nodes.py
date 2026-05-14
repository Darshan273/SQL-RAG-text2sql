import json
import re
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import Token
from functools import lru_cache
from typing import Any

from groq import AsyncGroq, DefaultAsyncHttpxClient
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlglot import exp, parse_one  # type: ignore[import]
from sqlglot.errors import ParseError

from app.config import get_settings
from app.db.connection import async_session_factory
from app.graph.state import AgentState, normalize_state
from app.schemas.registry import SCHEMA_SLICES, detect_required_tools, merge_slices
from app.schemas.semantic_router import semantic_route, get_schema_for_tools
from app.schemas.tool_definitions import TOOL_DEFINITIONS
from app.schemas.few_shots import FEW_SHOTS
from app.schemas.query_classifier import classify_query_type
from fastapi import Request


try:
    from blockbuster.blockbuster import blockbuster_skip
except ImportError:
    blockbuster_skip = None


WRITE_INTENT_KEYWORDS = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "REPLACE",
    "RENAME",
    "MERGE",
    "UPSERT",
    "GRANT",
    "REVOKE",
    "COMMIT",
    "ROLLBACK",
    "SAVEPOINT",
    "EXEC",
    "EXECUTE",
    "COPY",
    "VACUUM",
    "ANALYZE",
    "ATTACH",
    "DETACH",
    "PRAGMA",
    "SET",
    "RESET"
    "CREATE USER",
    "DROP USER",
    "ALTER USER",
    "CREATE DATABASE",
    "DROP DATABASE"
]

SQL_GENERATOR_SYSTEM_PROMPT = (
    "You are a PostgreSQL expert. Generate only SELECT SQL.\n"
    "Rules:\n"
    "- Explicit JOINs only with ON clause\n"
    "- Aliases: c=customers, o=orders, p=products, oi=order_items, pr=product_reviews\n"
    "- LEFT JOIN + WHERE IS NULL for never/no queries\n"
    "- GROUP BY for all aggregations\n"
    "- Return raw SQL only, no markdown"
)

SUPERVISOR_SYSTEM_PROMPT = """You are a query routing supervisor for a Text-to-SQL system.
Select exactly one tool that best matches the user's analytics question."""

FORMATTER_SYSTEM_PROMPT = (
    "Convert these DB results into a concise natural language answer. Be direct."
)


@lru_cache
def _groq_client() -> AsyncGroq:
    settings = get_settings()
    return AsyncGroq(
        api_key=settings.groq_api_key,
        http_client=DefaultAsyncHttpxClient(trust_env=False),
    )


def warm_runtime_clients() -> None:
    settings = get_settings()
    if settings.groq_api_key:
        _groq_client()


@contextmanager
def _allow_known_driver_setup_calls() -> Iterator[None]:
    if blockbuster_skip is None:
        yield
        return

    token: Token[bool] = blockbuster_skip.set(True)
    try:
        yield
    finally:
        blockbuster_skip.reset(token)

def _extract_tool_name(message: Any) -> str:
    tool_calls = getattr(message, "tool_calls", None)
    if not tool_calls:
        return ""

    first_tool_call = tool_calls[0]
    function = getattr(first_tool_call, "function", None)
    if function is None:
        return ""

    return getattr(function, "name", "") or ""


def _strip_sql_response(content: str) -> str:
    sql = content.strip()
    fenced_match = re.search(
        r"```(?:sql)?\s*(.*?)```",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if fenced_match:
        sql = fenced_match.group(1).strip()

    return sql.rstrip(";").strip()


def _append_limit_if_missing(sql: str, limit: int = 500) -> str:
    clean_sql = sql.strip().rstrip(";")
    if re.search(r"\blimit\b", clean_sql, flags=re.IGNORECASE):
        return f"{clean_sql};"
    return f"{clean_sql} LIMIT {limit};"


async def readonly_guard_node(state: AgentState) -> AgentState:
    state = normalize_state(state)
    user_query = state["user_query"]
    normalized_query = user_query.lower()
    has_write_intent = any(
        re.search(rf"\b{re.escape(keyword)}\b", normalized_query) is not None
        for keyword in WRITE_INTENT_KEYWORDS
    )

    next_state: AgentState = {**state}
    next_state["is_readonly_violation"] = has_write_intent

    if has_write_intent:
        next_state["error"] = "Write operations are not allowed. This system is read-only."
    else:
        next_state["error"] = ""

    return next_state


async def supervisor_node(state: AgentState) -> AgentState:
    state = normalize_state(state)
    client = _groq_client()
    
    try:
        matched_tools = await semantic_route(state["user_query"], client)
    except Exception as e:
        return {**state, "error": "Routing failed: " + str(e)}

    if len(matched_tools) == 1:
        tool_name = matched_tools[0]
    elif len(matched_tools) >= 2:
        tool_name = "query_cross_domain"
    elif matched_tools == ["query_cross_domain"]:
        tool_name = "query_cross_domain"
    else:
        tool_name = "query_cross_domain"

    schema_slice = get_schema_for_tools(matched_tools)

    return {**state, "tool_name": tool_name, "schema_slice": schema_slice, "error": ""}


async def sql_generator_node(state: AgentState) -> AgentState:
    state = normalize_state(state)
    settings = get_settings()
    client = _groq_client()
    
    query_type = classify_query_type(state["user_query"])
    examples = FEW_SHOTS.get(query_type, FEW_SHOTS["simple_select"])
    
    example_str = "Examples of correct SQL for similar queries:\n\n"
    for i, ex in enumerate(examples, 1):
        example_str += f"Query: {ex['question']}\nSQL: {ex['sql']}\n\n"
        
    user_content = (
        f"{example_str}"
        f"Now generate SQL for this query using this schema:\n"
        f"{state['schema_slice']}\n\n"
        f"Query: {state['user_query']}"
    )

    response = await client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": SQL_GENERATOR_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": user_content,
            },
        ],
        temperature=0,
    )

    next_state: AgentState = {**state}
    next_state["generated_sql"] = _strip_sql_response(
        response.choices[0].message.content or ""
    )
    return next_state


def validator_node(state: AgentState) -> AgentState:
    state = normalize_state(state)
    next_state: AgentState = {**state}

    try:
        expression = parse_one(state["generated_sql"], dialect="postgres")
    except ParseError as exc:
        next_state["validation_error"] = str(exc)
        return next_state

    if not isinstance(expression, exp.Select):
        next_state["is_readonly_violation"] = True
        next_state["error"] = "Generated SQL is not a SELECT statement. Blocked."
        next_state["validation_error"] = "Generated SQL is not a SELECT statement. Blocked."
        return next_state

    next_state["validation_error"] = ""
    next_state["error"] = ""
    return next_state


async def retry_node(state: AgentState) -> AgentState:
    state = normalize_state(state)
    settings = get_settings()
    client = _groq_client()

    response = await client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": SQL_GENERATOR_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"User question:\n{state['user_query']}\n\n"
                    f"Database schema:\n{state['schema_slice']}\n\n"
                    f"Previous SQL:\n{state['generated_sql']}\n\n"
                    "Previous SQL was invalid. Error: "
                    f"{state['validation_error']}\n"
                    "Fix it and return only valid SQL."
                ),
            },
        ],
        temperature=0,
    )

    next_state: AgentState = {**state}
    next_state["retry_count"] = state["retry_count"] + 1
    next_state["generated_sql"] = _strip_sql_response(
        response.choices[0].message.content or ""
    )
    return next_state


async def executor_node(state: AgentState) -> AgentState:
    state = normalize_state(state)
    next_state: AgentState = {**state}

    try:
        sql = _append_limit_if_missing(state["generated_sql"], limit=500)

        with _allow_known_driver_setup_calls():
            async with async_session_factory() as session:
                result = await session.execute(text(sql))
                rows = result.mappings().all()

        next_state["generated_sql"] = sql
        next_state["rows"] = [dict(row) for row in rows]
        next_state["error"] = ""
    except (SQLAlchemyError, ParseError, Exception) as exc:
        next_state["error"] = str(exc)

    return next_state


async def formatter_node(state: AgentState) -> AgentState:
    state = normalize_state(state)
    settings = get_settings()
    client = _groq_client()
    
    rows_sample = state["rows"][:10]
    total_count = state.get("total_count", len(state["rows"]))
    displayed = len(rows_sample)

    user_message = f"""User query: {state["user_query"]}

Total results found in database: {total_count}
Showing sample of {displayed} rows:
{json.dumps(rows_sample, indent=2, default=str)}

Instructions:
- Start your answer by clearly stating the total count
- Then summarize or list the sample rows shown
- If total > displayed, mention that only a sample is shown
- Be direct and concise"""

    response = await client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": "Convert database results into clear natural language.\nAlways mention total count first."},
            {
                "role": "user",
                "content": user_message,
            },
        ],
        temperature=0,
    )

    next_state: AgentState = {**state}
    next_state["answer"] = (response.choices[0].message.content or "").strip()
    return next_state
