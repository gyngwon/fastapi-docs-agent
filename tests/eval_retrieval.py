"""Retrieval quality evaluation — no Claude API key required.

For each (question, expected_source_file) pair, checks whether the expected
doc file appears in the top-k retrieved chunks. Reports hit-rate@1/3/5.

Usage:
    python -m tests.eval_retrieval
"""
import json
from pathlib import Path

from src.retriever import retrieve

EVAL_SET_PATH = Path(__file__).parent / "eval_questions.json"
K_VALUES = (1, 3, 5)


def run_eval() -> None:
    questions = json.loads(EVAL_SET_PATH.read_text())
    max_k = max(K_VALUES)

    hits = {k: 0 for k in K_VALUES}
    rows = []

    for item in questions:
        question = item["question"]
        expected = item["expected_source"]
        results = retrieve(question, top_k=max_k)
        retrieved_sources = [r.source_file for r in results]

        hit_rank = None
        for rank, src in enumerate(retrieved_sources, start=1):
            if src == expected:
                hit_rank = rank
                break

        for k in K_VALUES:
            if hit_rank is not None and hit_rank <= k:
                hits[k] += 1

        rows.append((question, expected, hit_rank))

    n = len(questions)
    print(f"Retrieval evaluation over {n} questions\n")
    for question, expected, rank in rows:
        mark = "✅" if rank == 1 else ("〜" if rank else "❌")
        print(f"{mark}  {question[:60]:<60}  expected={expected}  hit_rank={rank}")

    print("\nSummary:")
    for k in K_VALUES:
        rate = hits[k] / n * 100
        print(f"  hit-rate@{k}: {hits[k]}/{n} ({rate:.0f}%)")


if __name__ == "__main__":
    run_eval()
