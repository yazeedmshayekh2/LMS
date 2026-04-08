from langgraph.graph import StateGraph, END
from ....state import AgentState
from .nodes import assignment_maker_node

def build_assignment_graph():
    builder = StateGraph(AgentState)
    builder.add_node("run", assignment_maker_node)
    builder.set_entry_point("run")
    builder.add_edge("run", END)
    return builder.compile(debug=True)

assignment_graph = build_assignment_graph()