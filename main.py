from src import run_test
import asyncio


async def main():
    # Test 1: General question → respond
    await run_test("What is the difference between formative and summative assessment?")

    # Test 2: Assignment creation → assignment_maker
    await run_test("Create an assignment for grade 8 students about the water cycle.")

    # Test 3: Quiz generation → quiz_generator
    await run_test(
        "Generate a 5-question quiz about the French Revolution for high school."
    )

    # Test 4: Summarization → summarizer
    await run_test("Summarize the topic of photosynthesis for a 6th grade student.")


if __name__ == "__main__":
    asyncio.run(main())
