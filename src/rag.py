"""검색된 문서를 근거로 Claude가 답변을 생성하는 RAG 로직."""
from dataclasses import dataclass

from . import config
from .llm_client import get_client
from .retriever import RetrievedChunk, retrieve

SYSTEM_PROMPT = """\
You are a helpful assistant answering questions about the FastAPI web \
framework, using ONLY the documentation excerpts provided as context.

Rules:
- Answer using only the given context. If the context does not contain \
enough information, say so plainly instead of guessing.
- Cite every claim with the bracketed source number it came from, e.g. [1].
- Prefer short, direct, technically precise answers with code examples \
when the context includes them.
"""


def _format_context(chunks: list[RetrievedChunk]) -> str:
    parts = []
    for i, c in enumerate(chunks, start=1):
        loc = c.source_file + (f" > {c.header_path}" if c.header_path else "")
        parts.append(f"[{i}] (source: {loc})\n{c.text}")
    return "\n\n---\n\n".join(parts)


@dataclass
class RagAnswer:
    answer: str
    chunks: list[RetrievedChunk]


def generate_answer(query: str, top_k: int = config.TOP_K) -> RagAnswer:
    chunks = retrieve(query, top_k=top_k)
    context = _format_context(chunks)

    user_message = (
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        f"Answer using the context above, citing sources like [1]."
    )

    client = get_client()
    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    answer_text = "".join(
        block.text for block in response.content if block.type == "text"
    )
    return RagAnswer(answer=answer_text, chunks=chunks)
