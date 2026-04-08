from langchain_core.messages import SystemMessage

from ....state import AgentState
from ...llms import get_llm

from prompts import SUMMARIZER_PROMPT

def summarizer_node(state: AgentState):

    llm = get_llm(provider=state['llm_provider'])
    messages = [SystemMessage(content=SUMMARIZER_PROMPT)] + state['messages']
    response = llm.invoke(messages)

    return  {
        "messages": [response],
        "tool_result": {"tool": "summarizer", "content": response.content},
    }