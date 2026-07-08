from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401

from src.config import load_settings
from src.embeddings.embedding_client import EmbeddingClient
from src.graph.neo4j_client import Neo4jClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate embeddings for Chunk nodes.")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--limit", type=int, default=0, help="0 means no explicit limit")
    args = parser.parse_args()

    settings = load_settings()
    embedder = EmbeddingClient(settings)

    with Neo4jClient(settings) as client:
        total = 0
        while True:
            limit = args.batch_size if args.limit == 0 else min(args.batch_size, args.limit - total)
            if limit <= 0:
                break
            rows = client.query(
                """
                MATCH (c:Chunk)
                WHERE c.embedding IS NULL
                RETURN c.id AS id, c.text AS text
                ORDER BY c.chunk_index
                LIMIT $limit
                """,
                {"limit": limit},
            )
            if not rows:
                break

            embeddings = embedder.embed_texts([row["text"] for row in rows])
            update_rows = [
                {"id": row["id"], "embedding": embedding}
                for row, embedding in zip(rows, embeddings, strict=True)
            ]
            client.execute_many(
                """
                UNWIND $rows AS row
                MATCH (c:Chunk {id: row.id})
                SET c.embedding = row.embedding
                """,
                update_rows,
            )
            total += len(update_rows)
            print(f"Embedded {total} chunks...")

    print(f"Done. Embedded {total} chunks.")


if __name__ == "__main__":
    main()
