from langgraph.graph import StateGraph, END
from ....state import AgentState

from .nodes import summarizer_node

def build_summarizer_graph():
    builder=StateGraph(AgentState)
    builder.add_node("run", summarizer_node)
    builder.set_entry_point("run")
    builder.add_edge("run", END)
    return builder.compile(debug=True)

summarizer_graph = build_summarizer_graph()