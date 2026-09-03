"""Command-line entry point.

Usage:
    python -m src.cli "how do I use Depends for dependency injection?"
    python -m src.cli --plain "what is CORS?"        # plain RAG, no tool use
    python -m src.cli --retrieve-only "path params"   # skip Claude, no API key needed
"""
import argparse

from src.retriever import retrieve


def _print_chunks(chunks) -> None:
    for i, c in enumerate(chunks, start=1):
        print(f"\n[{i}] score={c.score:.3f}  {c.source_file}")
        preview = c.text[:300].replace("\n", " ")
        print(f"    {preview}...")


def main() -> None:
    parser = argparse.ArgumentParser(description="FastAPI docs RAG assistant")
    parser.add_argument("question", help="question to ask")
    parser.add_argument(
        "--plain", action="store_true",
        help="use plain RAG (single retrieve-then-generate call) instead of the agent",
    )
    parser.add_argument(
        "--retrieve-only", action="store_true",
        help="only run retrieval, don't call Claude (no API key needed)",
    )
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    if args.retrieve_only:
        chunks = retrieve(args.question, top_k=args.top_k)
        print(f"Top {len(chunks)} retrieved chunks for: {args.question!r}")
        _print_chunks(chunks)
        return

    if args.plain:
        from src.rag import generate_answer
        result = generate_answer(args.question, top_k=args.top_k)
        print("\n=== Answer (plain RAG) ===\n")
        print(result.answer)
        print("\n=== Sources ===")
        _print_chunks(result.chunks)
    else:
        from src.agent import answer_question
        result = answer_question(args.question)
        print("\n=== Answer (agent) ===\n")
        print(result.answer)
        if result.tool_calls:
            print("\n=== Tool calls ===")
            for tc in result.tool_calls:
                print(f"  - {tc.tool_name}({tc.tool_input})")


if __name__ == "__main__":
    main()
