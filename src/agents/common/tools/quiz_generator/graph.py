from langgraph.graph import StateGraph, END
from ....state import AgentState

from .nodes import quiz_generator_node

def build_quiz_generator_graph():
    builder=StateGraph(AgentState)
    builder.add_node("run", quiz_generator_node)
    builder.set_entry_point("run")
    builder.add_edge("run", END)
    return builder.compile()

quiz_graph = build_quiz_generator_graph()