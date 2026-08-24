"""마크다운 문서를 헤더 기준으로 먼저 나누고, 너무 긴 섹션은 겹치는
슬라이딩 윈도우로 다시 쪼개는 청킹 로직."""
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from . import config

HEADER_RE = re.compile(r"^(#{1,4})\s+(.*)$", re.MULTILINE)

# 사용법 설명이 아닌 파일(체인지로그, 내부 테스트용 등)은 검색 노이즈만
# 키우므로 청킹 대상에서 제외한다.
EXCLUDED_FILES = {"release-notes.md", "_llm-test.md"}


@dataclass
class Chunk:
    text: str
    source_file: str
    header_path: str
    chunk_index: int

    def id(self) -> str:
        # 위치(chunk_index) 대신 내용 기반 해시를 ID로 쓴다.
        # 문서 앞부분이 수정돼서 뒤 청크들의 인덱스가 밀려도
        # 벡터스토어 upsert가 안정적으로 동작한다.
        digest = hashlib.sha256(
            f"{self.source_file}::{self.text}".encode()
        ).hexdigest()
        return f"{self.source_file}::{digest[:16]}"


def _split_by_headers(text: str) -> list[tuple[str, str]]:
    matches = list(HEADER_RE.finditer(text))
    if not matches:
        return [("", text)]

    sections = []
    breadcrumb_stack: list[tuple[int, str]] = []
    prefix = text[: matches[0].start()].strip()

    for i, m in enumerate(matches):
        level = len(m.group(1))
        title = m.group(2).strip(" {}#").strip()

        breadcrumb_stack = [h for h in breadcrumb_stack if h[0] < level]
        breadcrumb_stack.append((level, title))
        breadcrumb = " > ".join(t for _, t in breadcrumb_stack)

        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[start:end].strip()

        if i == 0 and prefix:
            section_text = f"{prefix}\n\n{section_text}".strip()

        if section_text:
            sections.append((breadcrumb, section_text))

    return sections


def _sliding_window(text: str, size: int, overlap: int) -> list[str]:
    if overlap >= size:
        raise ValueError(
            f"CHUNK_OVERLAP_CHARS({overlap}) must be < CHUNK_SIZE_CHARS({size}), "
            "otherwise the window never advances"
        )

    if len(text) <= size:
        return [text]

    windows = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        windows.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return windows


def chunk_markdown_file(path: Path, root: Path) -> list[Chunk]:
    rel_path = str(path.relative_to(root))

    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as e:
        print(f"[chunking] WARNING: failed to read {rel_path}: {e}")
        return []

    sections = _split_by_headers(raw)

    chunks: list[Chunk] = []
    idx = 0
    for breadcrumb, section_text in sections:
        for window in _sliding_window(
            section_text, config.CHUNK_SIZE_CHARS, config.CHUNK_OVERLAP_CHARS
        ):
            window = window.strip()
            if len(window) < 40:
                continue
            chunks.append(
                Chunk(
                    text=window,
                    source_file=rel_path,
                    header_path=breadcrumb,
                    chunk_index=idx,
                )
            )
            idx += 1
    return chunks


def chunk_all_docs(root: Path) -> list[Chunk]:
    all_chunks: list[Chunk] = []
    for path in sorted(root.rglob("*.md")):
        if path.name in EXCLUDED_FILES:
            continue
        all_chunks.extend(chunk_markdown_file(path, root))
    return all_chunks
