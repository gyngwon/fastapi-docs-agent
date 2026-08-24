"""질문이 들어오면 벡터 검색으로 관련 청크를 찾아온다."""
from dataclasses import dataclass

import chromadb

from . import config
from .embeddings import embed_texts

_collection = None


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(config.CHROMA_DB_DIR))
        _collection = client.get_collection(config.COLLECTION_NAME)
    return _collection


@dataclass
class RetrievedChunk:
    text: str
    source_file: str
    header_path: str
    score: float


def retrieve(query: str, top_k: int = config.TOP_K) -> list[RetrievedChunk]:
    collection = _get_collection()
    query_embedding = embed_texts([query])

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    out = []
    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        out.append(
            RetrievedChunk(
                text=doc,
                source_file=meta.get("source_file", ""),
                header_path=meta.get("header_path", ""),
                score=1 - dist,  # 코사인 거리를 유사도로 변환
            )
        )
    return out
