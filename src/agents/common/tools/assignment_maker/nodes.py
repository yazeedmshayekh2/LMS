from langchain_core.messages import SystemMessage

from ....state import AgentState
from .....ai import get_llm

from .prompts import ASSIGNMENT_MAKER_PROMPT


def assignment_maker_node(state: AgentState) -> dict:
    llm = get_llm(provider=state["llm_provider"])
    messages = [SystemMessage(content=ASSIGNMENT_MAKER_PROMPT)] + state["messages"]
    response = llm.invoke(messages)

    return {
        "messages": [response],
        "tool_result": {"tool": "assignment_maker", "content": response.content},
    }
