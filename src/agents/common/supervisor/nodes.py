from langchain_core.messages import SystemMessage
from ...state import AgentState
from ....ai import get_llm
from langchain.tools import tool

from ..tools import *  # Import the general tools

from .prompts import (
    SUPERVISOR_PROMPT,
)  # Import the prompts that must be used in the nodes


@tool
def route_to(tool_name: str) -> str:
    """Route the user's request to the correct tool."""
    return tool_name


def supervisor_node(state: AgentState) -> dict:
    """This node is reposible about using the supervisor prompt to route the state to the next proper node based on the user's question"""
    llm = get_llm(provider=state["llm_provider"])
    tools = [route_to]
    llm_with_tools = llm.bind_tools(tools=tools)

    messages = [SystemMessage(content=SUPERVISOR_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)

    if response.tool_calls:
        print("Response Tool Calls: ", response.tool_calls[0])
        next_node = response.tool_calls[0]["args"]["tool_name"]
    else:
        next_node = "respond"

    return {"next": next_node}


def respond_node(state: AgentState) -> dict:
    """Handles general questions directly without routing to a tool."""
    llm = get_llm(provider=state["llm_provider"])
    messages = [SystemMessage(content=SUPERVISOR_PROMPT)] + state["messages"]
    response = llm.invoke(messages)

    return {
        "messages": [response],
        "tools": None,
    }
