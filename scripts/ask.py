from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401

from src.config import load_settings
from src.embeddings.embedding_client import EmbeddingClient
from src.graph.neo4j_client import Neo4jClient
from src.qa.answer_generator import AnswerGenerator
from src.retrieval.vector_retriever import VectorRetriever


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask a question about ingested PDFs.")
    parser.add_argument("question")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    settings = load_settings()
    embedder = EmbeddingClient(settings)
    answerer = AnswerGenerator(settings)
    with Neo4jClient(settings) as client:
        retriever = VectorRetriever(settings, client, embedder)
        chunks = retriever.search(args.question, args.top_k)

    print(answerer.answer(args.question, chunks))


if __name__ == "__main__":
    main()
