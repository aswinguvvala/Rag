import asyncio
from integrated_optimized_system import OptimizedRAGSystem


async def main():
    system = OptimizedRAGSystem()
    await system.initialize()
    await system.initialize_optimization(base_model="microsoft/phi-2")

    test_queries = [
        "What is space?",
        "Explain quantum mechanics and its applications",
        "Write a Python function to implement a neural network from scratch"
    ]

    for q in test_queries:
        result = await system.search_query_optimized(q)
        print(f"\nQuery: {q}")
        opt = result.get('optimization') or {}
        print(f"Model Used: {opt.get('model_used', 'N/A')}")
        if opt:
            print(f"Quality: {opt.get('quality_score', 0):.2f}")
            print(f"Speed: {opt.get('tokens_per_second', 0):.1f} tok/s")


if __name__ == "__main__":
    asyncio.run(main())


