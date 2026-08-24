"""data/raw_docs를 청킹 + 임베딩해서 Chroma 벡터DB를 만든다.

실행: python -m src.ingest
"""
import chromadb
from tqdm import tqdm

from . import config
from .chunking import chunk_all_docs
from .embeddings import embed_texts


def build_index():
    config.CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)

    print("[1/2] 문서 청킹 중...")
    chunks = chunk_all_docs(config.RAW_DOCS_DIR)
    print(f"  -> 청크 {len(chunks)}개")

    print("[2/2] 임베딩 + Chroma 저장 중...")
    client = chromadb.PersistentClient(path=str(config.CHROMA_DB_DIR))
    collection = client.get_or_create_collection(
        name=config.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    batch_size = 64
    for i in tqdm(range(0, len(chunks), batch_size)):
        batch = chunks[i : i + batch_size]
        texts = [c.text for c in batch]
        embeddings = embed_texts(texts)
        collection.upsert(
            ids=[c.id() for c in batch],
            embeddings=embeddings,
            documents=texts,
            metadatas=[
                {"source_file": c.source_file, "header_path": c.header_path}
                for c in batch
            ],
        )

    print(f"완료. {len(chunks)}개 청크를 {config.CHROMA_DB_DIR}에 저장했어요.")


if __name__ == "__main__":
    build_index()
