from __future__ import annotations

from dataclasses import dataclass

from src.config import Settings
from src.embeddings.embedding_client import EmbeddingClient
from src.graph.neo4j_client import Neo4jClient


@dataclass(frozen=True)
class RetrievedChunk:
    id: str
    text: str
    page_number: int
    chunk_index: int
    score: float


class VectorRetriever:
    def __init__(self, settings: Settings, client: Neo4jClient, embedder: EmbeddingClient):
        self._settings = settings
        self._client = client
        self._embedder = embedder

    def search(self, question: str, top_k: int = 5) -> list[RetrievedChunk]:
        embedding = self._embedder.embed_query(question)
        rows = self._client.query(
            """
            CALL db.index.vector.queryNodes($index_name, $top_k, $embedding)
            YIELD node, score
            RETURN node.id AS id,
                   node.text AS text,
                   node.page_number AS page_number,
                   node.chunk_index AS chunk_index,
                   score
            ORDER BY score DESC
            """,
            {
                "index_name": self._settings.vector_index_name,
                "top_k": top_k,
                "embedding": embedding,
            },
        )
        return [
            RetrievedChunk(
                id=row["id"],
                text=row["text"],
                page_number=row["page_number"],
                chunk_index=row["chunk_index"],
                score=row["score"],
            )
            for row in rows
        ]
