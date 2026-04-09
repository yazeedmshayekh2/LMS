from langgraph.graph import StateGraph, END
from ....state import AgentState
from .nodes import assignment_maker_node

from ....state import LLMProvider


def build_assignment_graph():
    builder = StateGraph(AgentState)
    builder.add_node("run", assignment_maker_node)
    builder.set_entry_point("run")
    builder.add_edge("run", END)
    return builder.compile(debug=True)


assignment_graph = build_assignment_graph()


# import asyncio

# from dotenv import load_dotenv, find_dotenv

# load_dotenv(find_dotenv())


# async def run_test(user_message: str, provider: LLMProvider = LLMProvider.GPT):
#     initial_state = {
#         "messages": [("user", user_message)],
#         "user_id": "test-user-01",
#         "user_role": "teacher",
#         "llm_provider": provider,
#         "next": None,
#         "tool_result": None,
#     }

#     print(f"\n{'='*60}")
#     print(f"USER  : {user_message}")
#     print(f"MODEL : {provider.value}")
#     print(f"{'='*60}\n")

#     async for event in assignment_graph.astream(initial_state, stream_mode="updates"):
#         for node_name, node_output in event.items():
#             print(f"[NODE: {node_name}]")

#             if "next" in node_output and node_output["next"]:
#                 print(f"  → Routing to: {node_output['next']}")

#             if "tool_result" in node_output and node_output["tool_result"]:
#                 print(f"  → Tool used : {node_output['tool_result']['tool']}")

#             if "messages" in node_output:
#                 for msg in node_output["messages"]:
#                     if hasattr(msg, "content") and msg.content:
#                         print(f"\nRESPONSE:\n{msg.content}\n")

#     print(f"{'='*60}\n")


# if __name__ == "__main__":
#     asyncio.run(
#         run_test("Create an assignment for grade 8 students about the water cycle.")
#     )
