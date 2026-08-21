"""프로젝트 전체 설정값. 나중 단계에서 계속 추가될 예정."""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# --- 경로 ---
RAW_DOCS_DIR = ROOT_DIR / "data" / "raw_docs"

# --- 청킹 ---
CHUNK_SIZE_CHARS = 1200   # 한 청크 최대 글자 수
CHUNK_OVERLAP_CHARS = 200  # 슬라이딩 윈도우 겹치는 글자 수