import sqlglot
from sqlglot import exp, parse_one
from sqlglot.errors import ParseError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.connection import async_session_factory
from app.graph.state import AgentState, normalize_state
from app.graph.nodes import _allow_known_driver_setup_calls

def should_append_limit(sql: str) -> bool:
    try:
        expression = parse_one(sql, dialect="postgres")
    except Exception:
        return True
        
    if expression.args.get("limit"):
        return False
        
    for node in expression.find_all(exp.AggFunc):
        if isinstance(node, (exp.Count, exp.Sum, exp.Avg, exp.Max, exp.Min)):
            return False
            
    return True

async def executor_node(state: AgentState) -> AgentState:
    state = normalize_state(state)
    next_state: AgentState = {**state}

    original_sql = state["generated_sql"].strip().rstrip(";")
    total_count = 0

    try:
        count_sql = f"SELECT COUNT(*) FROM ({original_sql}) AS _count_subquery"
        with _allow_known_driver_setup_calls():
            async with async_session_factory() as session:
                result = await session.execute(text(count_sql))
                total_count = result.scalar() or 0
    except Exception:
        total_count = 0

    try:
        sql = original_sql
        if should_append_limit(sql):
            sql = f"{original_sql} LIMIT 500"
            
        with _allow_known_driver_setup_calls():
            async with async_session_factory() as session:
                result = await session.execute(text(sql))
                rows = result.mappings().all()

        next_state["generated_sql"] = sql
        next_state["rows"] = [dict(row) for row in rows]
        next_state["total_count"] = total_count
        next_state["error"] = ""
    except (SQLAlchemyError, ParseError, Exception) as exc:
        next_state["error"] = str(exc)

    return next_state
