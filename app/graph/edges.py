from app.graph.state import AgentState


def route_after_guard(state: AgentState) -> str:
    if state.get("is_readonly_violation"):
        return "end_with_error"

    return "supervisor"


def route_after_supervisor(state: AgentState) -> str:
    if state.get("error"):
        return "end_with_error"

    return "sql_generator"


def route_after_validation(state: AgentState) -> str:
    if state.get("is_readonly_violation"):
        return "end_with_error"

    if state.get("validation_error", "") == "":
        return "executor"

    if state.get("retry_count", 0) < 1:
        return "retry"

    return "end_with_error"
