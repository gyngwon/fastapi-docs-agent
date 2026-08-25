"""에이전트형 RAG: Claude가 도구 사용을 스스로 판단한다."""
from dataclasses import dataclass, field

from . import config
from .llm_client import get_client
from .retriever import RetrievedChunk, retrieve
from .tools.github_search import search_github_issues

MAX_TOOL_ITERATIONS = 5

AGENT_SYSTEM_PROMPT = """\
You are a technical assistant for the FastAPI web framework.

You have two tools:
- search_docs: searches the official FastAPI documentation. Always try \
this first for "how do I..." / usage questions.
- search_github_issues: searches GitHub issues/PRs on the fastapi/fastapi \
repo. Use this only when the documentation doesn't answer the question.

Rules:
- Ground every answer in tool results. If neither tool helps, say so.
- Cite sources inline: [doc: <source_file>] or [gh: <issue url>].
"""

TOOLS = [
    {
        "name": "search_docs",
        "description": "Semantic search over the official FastAPI documentation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_github_issues",
        "description": "Search GitHub issues/PRs on fastapi/fastapi for bugs or edge cases.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
]


@dataclass
class ToolCallRecord:
    tool_name: str
    tool_input: dict
    result_summary: str


@dataclass
class AgentAnswer:
    answer: str
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    retrieved_chunks: list[RetrievedChunk] = field(default_factory=list)


def _execute_tool(name: str, tool_input: dict, trace: AgentAnswer) -> str:
    if name == "search_docs":
        query = tool_input["query"]
        top_k = tool_input.get("top_k", config.TOP_K)
        chunks = retrieve(query, top_k=top_k)
        trace.retrieved_chunks.extend(chunks)
        trace.tool_calls.append(
            ToolCallRecord("search_docs", tool_input, f"{len(chunks)} chunk(s)")
        )
        if not chunks:
            return "No results found."
        return "\n\n".join(
            f"[{c.source_file} > {c.header_path}]\n{c.text}" for c in chunks
        )

    if name == "search_github_issues":
        query = tool_input["query"]
        results = search_github_issues(query)
        if results and "error" in results[0]:
            trace.tool_calls.append(
                ToolCallRecord("search_github_issues", tool_input, f"error: {results[0]['error']}")
            )
            return f"GitHub search failed: {results[0]['error']}"
        trace.tool_calls.append(
            ToolCallRecord("search_github_issues", tool_input, f"{len(results)} issue(s)")
        )
        if not results:
            return "No matching issues found."
        return "\n\n".join(
            f"- [{r['state']}] {r['title']} ({r['url']})\n  {r['snippet']}"
            for r in results
        )

    return f"Unknown tool: {name}"


def answer_question(query: str) -> AgentAnswer:
    client = get_client()
    trace = AgentAnswer(answer="")
    messages = [{"role": "user", "content": query}]

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=1536,
            system=AGENT_SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            trace.answer = "".join(
                b.text for b in response.content if b.type == "text"
            )
            return trace

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result_text = _execute_tool(block.name, block.input, trace)
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": result_text}
            )
        messages.append({"role": "user", "content": tool_results})

    trace.answer = "(tool-call 한도에 도달해서 최종 답변을 못 냈어요)"
    return trace
