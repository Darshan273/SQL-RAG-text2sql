from pydantic import BaseModel, ConfigDict


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    sql: str
    tool_used: str
    row_count: int
    total_count: int
    readonly_violation: bool


class ErrorResponse(BaseModel):
    error: str
    detail: str


class ToolInfo(BaseModel):
    name: str
    description: str

    model_config = ConfigDict(extra="forbid")
