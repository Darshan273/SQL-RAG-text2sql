from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    user_query: str
    tool_name: str
    schema_slice: str
    generated_sql: str
    validation_error: str
    retry_count: int
    rows: list[dict]
    total_count: int
    answer: str
    error: str
    is_readonly_violation: bool


def default_agent_state(user_query: str = "") -> AgentState:
    return {
        "user_query": user_query,
        "tool_name": "",
        "schema_slice": "",
        "generated_sql": "",
        "validation_error": "",
        "retry_count": 0,
        "rows": [],
        "total_count": 0,
        "answer": "",
        "error": "",
        "is_readonly_violation": False,
    }


def normalize_state(state: AgentState) -> AgentState:
    normalized_state = default_agent_state(state.get("user_query", ""))
    normalized_state.update(state)
    return normalized_state
