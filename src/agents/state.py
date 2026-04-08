from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import add_messages

from common import LLMProvider

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: str
    user_role: Literal['student', 'teacher']
    llm_provider: LLMProvider
    next: str | None
    tool_result: str | None