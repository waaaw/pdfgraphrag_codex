from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401

from src.config import load_settings
from src.graph.neo4j_client import Neo4jClient
from src.kg.graph_builder import build_mentions_for_existing_chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a lightweight Entity mention graph.")
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()

    settings = load_settings()
    with Neo4jClient(settings) as client:
        count = build_mentions_for_existing_chunks(client, args.limit)

    print(f"Created or matched {count} Chunk-[:MENTIONS]->Entity relationships.")


if __name__ == "__main__":
    main()
