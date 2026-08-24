import pytest

from src.chunking import _sliding_window, _split_by_headers, chunk_all_docs


def test_sliding_window_no_split_needed():
    assert _sliding_window("short text", size=100, overlap=10) == ["short text"]


def test_sliding_window_windows_overlap_correctly():
    text = "a" * 250
    windows = _sliding_window(text, size=100, overlap=20)
    # 연속된 두 윈도우가 실제로 20자만큼 겹치는지 확인
    assert windows[0][-20:] == windows[1][:20]


def test_sliding_window_rejects_overlap_gte_size():
    with pytest.raises(ValueError):
        _sliding_window("a" * 500, size=100, overlap=100)


def test_split_by_headers_breadcrumb_nesting():
    text = "# Title\nintro\n## Sub\nsub content\n### Deep\ndeep content"
    sections = _split_by_headers(text)
    breadcrumbs = [b for b, _ in sections]
    assert breadcrumbs[0] == "Title"
    assert breadcrumbs[1] == "Title > Sub"
    assert breadcrumbs[2] == "Title > Sub > Deep"


def test_chunk_all_docs_skips_excluded_files(tmp_path):
    (tmp_path / "release-notes.md").write_text("# ignored\n" + "x" * 100)
    (tmp_path / "guide.md").write_text(
        "# Guide\nsome real content here that is long enough to keep"
    )
    chunks = chunk_all_docs(tmp_path)
    assert all(c.source_file != "release-notes.md" for c in chunks)
    assert any(c.source_file == "guide.md" for c in chunks)
