import asyncio
from src.agents.common.supervisor.graph import build_supervisor_graph
from src.agents.common.llms.enums import LLMProvider

# Build graph once without checkpointer
graph = build_supervisor_graph()

async def run_test(user_message: str, provider: LLMProvider = LLMProvider.GPT):
    initial_state = {
        "messages":     [("user", user_message)],
        "user_id":      "test-user-01",
        "user_role":    "teacher",
        "llm_provider": provider,
        "next":         None,
        "tool_result":  None,
    }

    print(f"\n{'='*60}")
    print(f"USER  : {user_message}")
    print(f"MODEL : {provider.value}")
    print(f"{'='*60}\n")

    async for event in graph.astream(initial_state, stream_mode="updates"):
        for node_name, node_output in event.items():
            print(f"[NODE: {node_name}]")

            if "next" in node_output and node_output["next"]:
                print(f"  → Routing to: {node_output['next']}")

            if "tool_result" in node_output and node_output["tool_result"]:
                print(f"  → Tool used : {node_output['tool_result']['tool']}")

            if "messages" in node_output:
                for msg in node_output["messages"]:
                    if hasattr(msg, "content") and msg.content:
                        print(f"\nRESPONSE:\n{msg.content}\n")

    print(f"{'='*60}\n")


async def main():
    # Test 1: General question → respond
    await run_test("What is the difference between formative and summative assessment?")

    # Test 2: Assignment creation → assignment_maker
    await run_test("Create an assignment for grade 8 students about the water cycle.")

    # Test 3: Quiz generation → quiz_generator
    await run_test("Generate a 5-question quiz about the French Revolution for high school.")

    # Test 4: Summarization → summarizer
    await run_test("Summarize the topic of photosynthesis for a 6th grade student.")


if __name__ == "__main__":
    asyncio.run(main())