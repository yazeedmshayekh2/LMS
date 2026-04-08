from langgraph.graph import StateGraph, START, END
from ...state import AgentState
from ..supervisor.nodes import supervisor_node, respond_node
from ..supervisor.edges import route_next
from ..tools.assignment_maker import assignment_graph
from ..tools.quiz_generator import quiz_graph
from ..tools.summarizer import summarizer_graph
from .enums import ValidRoutesEnum

def build_supervisor_graph(checkpointer=None):
    builder=StateGraph(AgentState)
    builder.add_node("supervisor", supervisor_node)

    builder.add_node("assignment_maker", assignment_graph)
    builder.add_node("quiz_generator",   quiz_graph)
    builder.add_node("summarizer",       summarizer_graph)
    builder.add_node("respond", respond_node)

    builder.add_edge(START, "supervisor")

    builder.add_conditional_edges(
        "supervisor",
        route_next,
        {
            ValidRoutesEnum.ASSIGNMENTMAKER.value: "assignment_maker",
            ValidRoutesEnum.QUIZGENERATOR.value: "quiz_generator",
            ValidRoutesEnum.SUMMARIZER.value: "summarizer",
            ValidRoutesEnum.RESPOND.value: "respond"
        }
    )

    builder.add_edge("assignment_maker", END)
    builder.add_edge("quiz_generator", END)
    builder.add_edge("summarizer", END)
    builder.add_edge("respond", END)

    return builder.compile(
        checkpointer=checkpointer,
        debug=True
    )
