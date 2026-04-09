from langchain_core.messages import SystemMessage

from ....state import AgentState
from .....ai import get_llm

from .prompts import QUIZ_GENERATOR_PROMPT


def quiz_generator_node(state: AgentState):

    llm = get_llm(provider=state["llm_provider"])
    messages = [SystemMessage(content=QUIZ_GENERATOR_PROMPT)] + state["messages"]
    response = llm.invoke(messages)

    return {
        "messages": [response],
        "tool_result": {"tool": "quiz_generator", "content": response.content},
    }
