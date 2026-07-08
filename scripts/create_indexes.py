from __future__ import annotations

import _bootstrap  # noqa: F401

from src.config import load_settings
from src.graph.neo4j_client import Neo4jClient
from src.graph.schema import create_schema


def main() -> None:
    settings = load_settings()
    with Neo4jClient(settings) as client:
        client.verify_connectivity()
        create_schema(client, settings)
    print("Neo4j constraints and vector index are ready.")


if __name__ == "__main__":
    main()
