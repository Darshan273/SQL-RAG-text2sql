from langgraph.graph import END, START, StateGraph

from app.graph.edges import (
    route_after_guard,
    route_after_supervisor,
    route_after_validation,
)
from app.graph.nodes import (
    formatter_node,
    readonly_guard_node,
    retry_node,
    sql_generator_node,
    supervisor_node,
    validator_node,
    warm_runtime_clients,
)
from app.db.executor import executor_node
from app.graph.state import AgentState


builder = StateGraph(AgentState)

builder.add_node("read_only_guard", readonly_guard_node)
builder.add_node("supervisor", supervisor_node)
builder.add_node("sql_generator", sql_generator_node)
builder.add_node("validator", validator_node)
builder.add_node("retry", retry_node)
builder.add_node("executor", executor_node)
builder.add_node("formatter", formatter_node)

builder.add_edge(START, "read_only_guard")
builder.add_conditional_edges(
    "read_only_guard",
    route_after_guard,
    {
        "end_with_error": END,
        "supervisor": "supervisor",
    },
)
builder.add_conditional_edges(
    "supervisor",
    route_after_supervisor,
    {
        "end_with_error": END,
        "sql_generator": "sql_generator",
    },
)
builder.add_edge("sql_generator", "validator")
builder.add_conditional_edges(
    "validator",
    route_after_validation,
    {
        "executor": "executor",
        "retry": "retry",
        "end_with_error": END,
    },
)
builder.add_edge("retry", "validator")
builder.add_edge("executor", "formatter")
builder.add_edge("formatter", END)

graph = builder.compile()
warm_runtime_clients()
