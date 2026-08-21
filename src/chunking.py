"""마크다운 문서를 헤더 기준으로 먼저 나누고, 너무 긴 섹션은 겹치는
슬라이딩 윈도우로 다시 쪼개는 청킹 로직."""
import re
from dataclasses import dataclass
from pathlib import Path

from . import config


@dataclass
class Chunk:
    text: str
    source_file: str
    header_path: str
    chunk_index: int

    def id(self) -> str:
        return f"{self.source_file}::{self.chunk_index}"


# '#', '##', '###', '####' 로 시작하는 줄을 찾는 정규식
HEADER_RE = re.compile(r"^(#{1,4})\s+(.*)$", re.MULTILINE)


def _split_by_headers(text: str) -> list[tuple[str, str]]:
    """헤더 기준으로 (헤더_경로, 섹션_본문) 튜플 리스트를 반환한다."""
    matches = list(HEADER_RE.finditer(text))
    if not matches:
        # 헤더가 하나도 없으면 문서 전체를 섹션 하나로 취급
        return [("", text)]

    sections = []
    breadcrumb_stack: list[tuple[int, str]] = []  # (헤더 레벨, 제목)

    # 첫 헤더보다 앞에 있는 텍스트(드물게 있는 서문 등)
    prefix = text[: matches[0].start()].strip()

    for i, m in enumerate(matches):
        level = len(m.group(1))          # '#' 개수 = 헤더 레벨
        title = m.group(2).strip(" {}#").strip()

        # 지금 헤더보다 레벨이 같거나 깊은 이전 헤더들은 breadcrumb에서 제거
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
    """text가 size보다 길면, overlap만큼 겹치며 size 단위로 자른다."""
    if len(text) <= size:
        return [text]

    windows = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        windows.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap  # 다음 윈도우는 overlap만큼 겹치게 시작
    return windows


def chunk_markdown_file(path: Path, root: Path) -> list[Chunk]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    rel_path = str(path.relative_to(root))
    sections = _split_by_headers(raw)

    chunks: list[Chunk] = []
    idx = 0
    for breadcrumb, section_text in sections:
        for window in _sliding_window(
            section_text, config.CHUNK_SIZE_CHARS, config.CHUNK_OVERLAP_CHARS
        ):
            window = window.strip()
            if len(window) < 40:  # 너무 짧은 조각은 의미가 없어서 스킵
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
        all_chunks.extend(chunk_markdown_file(path, root))
    return all_chunks