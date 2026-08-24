"""텍스트를 로컬 sentence-transformers 모델로 임베딩(벡터화)한다."""
from sentence_transformers import SentenceTransformer

from . import config

_model = None  # 모델을 한 번만 로드해서 재사용하기 위한 캐시


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
    return _model


def embed_texts(texts: list[str]):
    """텍스트 리스트를 받아서 벡터(임베딩) 리스트를 반환한다."""
    model = get_model()
    return model.encode(texts, show_progress_bar=False).tolist()
