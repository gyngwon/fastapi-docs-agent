"""프로젝트 전체 설정값. 나중 단계에서 계속 추가될 예정."""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# --- 경로 ---
RAW_DOCS_DIR = ROOT_DIR / "data" / "raw_docs"

# --- 청킹 ---
CHUNK_SIZE_CHARS = 1200
CHUNK_OVERLAP_CHARS = 200

assert CHUNK_OVERLAP_CHARS < CHUNK_SIZE_CHARS, (
    "CHUNK_OVERLAP_CHARS must be smaller than CHUNK_SIZE_CHARS, "
    "otherwise chunking will loop forever"
)