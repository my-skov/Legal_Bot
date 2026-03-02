from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    metadata: dict[str, Any]
    score: float


class VectorKnowledgeBase:
    def __init__(self, db_path: Path, config_path: Path, top_k: int = 5) -> None:
        self.db_path = db_path
        self.config_path = config_path
        self.top_k = top_k

        self.config = self._load_config()
        self.query_prefix = self.config.get("e5_prefix", {}).get("query", "")
        embedding_model = self.config.get(
            "embedding_model", "intfloat/multilingual-e5-base"
        )

        self.model = SentenceTransformer(embedding_model)
        self.client = chromadb.PersistentClient(path=str(self.db_path))

    def _load_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            return {}
        with self.config_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def retrieve(self, question: str) -> list[RetrievedChunk]:
        query_text = f"{self.query_prefix}{question}".strip()
        query_embedding = self.model.encode(query_text, normalize_embeddings=True).tolist()

        all_chunks: list[RetrievedChunk] = []
        collections = self.client.list_collections()
        if not collections:
            return []

        for collection_info in collections:
            collection = self.client.get_collection(collection_info.name)
            result = collection.query(
                query_embeddings=[query_embedding],
                n_results=self.top_k,
                include=["documents", "metadatas", "distances"],
            )
            docs = (result.get("documents") or [[]])[0]
            metas = (result.get("metadatas") or [[]])[0]
            distances = (result.get("distances") or [[]])[0]

            for idx, doc in enumerate(docs):
                all_chunks.append(
                    RetrievedChunk(
                        text=doc or "",
                        metadata=metas[idx] if idx < len(metas) and metas[idx] else {},
                        score=float(distances[idx]) if idx < len(distances) else 1.0,
                    )
                )

        all_chunks.sort(key=lambda chunk: chunk.score)
        return all_chunks[: self.top_k]

