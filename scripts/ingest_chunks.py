from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401

from src.config import load_settings
from src.graph.ingest import ingest_document_chunks
from src.graph.neo4j_client import Neo4jClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest PDF chunks into Neo4j.")
    parser.add_argument("chunks_json", help="Path to chunks.json")
    args = parser.parse_args()

    payload = json.loads(Path(args.chunks_json).read_text(encoding="utf-8"))
    settings = load_settings()
    with Neo4jClient(settings) as client:
        ingest_document_chunks(client, payload)

    print(f"Ingested {len(payload['chunks'])} chunks into Neo4j.")


if __name__ == "__main__":
    main()
