from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401

from src.config import load_settings
from src.embeddings.embedding_client import EmbeddingClient
from src.graph.neo4j_client import Neo4jClient
from src.preprocessing.text_cleaner import text_preview
from src.retrieval.vector_retriever import VectorRetriever


def main() -> None:
    parser = argparse.ArgumentParser(description="Search chunks with Neo4j vector index.")
    parser.add_argument("question")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    settings = load_settings()
    embedder = EmbeddingClient(settings)
    with Neo4jClient(settings) as client:
        retriever = VectorRetriever(settings, client, embedder)
        results = retriever.search(args.question, args.top_k)

    for index, chunk in enumerate(results, start=1):
        print(f"\n[{index}] score={chunk.score:.4f} page={chunk.page_number} chunk={chunk.chunk_index}")
        print(text_preview(chunk.text, 500))


if __name__ == "__main__":
    main()
