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
# --- 임베딩 / 벡터스토어 ---
CHROMA_DB_DIR = ROOT_DIR / "data" / "chroma_db"
COLLECTION_NAME = "fastapi_docs"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 5

# --- Claude API ---
import os
from dotenv import load_dotenv

load_dotenv(ROOT_DIR / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")

# --- GitHub issue search tool ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = "fastapi/fastapi"
