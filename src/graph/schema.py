from __future__ import annotations

import re

from src.config import Settings
from src.graph.neo4j_client import Neo4jClient


_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def safe_identifier(value: str) -> str:
    if not _SAFE_IDENTIFIER.match(value):
        raise ValueError(f"Unsafe Neo4j identifier: {value}")
    return value


def create_constraints(client: Neo4jClient) -> None:
    statements = [
        "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
        "CREATE CONSTRAINT page_id IF NOT EXISTS FOR (p:Page) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT entity_key IF NOT EXISTS FOR (e:Entity) REQUIRE e.normalized_name IS UNIQUE",
    ]
    for statement in statements:
        client.execute_write(statement)


def create_vector_index(client: Neo4jClient, settings: Settings) -> None:
    index_name = safe_identifier(settings.vector_index_name)
    statement = f"""
    CREATE VECTOR INDEX {index_name} IF NOT EXISTS
    FOR (c:Chunk)
    ON (c.embedding)
    OPTIONS {{
      indexConfig: {{
        `vector.dimensions`: {settings.embedding_dimensions},
        `vector.similarity_function`: 'cosine'
      }}
    }}
    """
    client.execute_write(statement)


def create_schema(client: Neo4jClient, settings: Settings) -> None:
    create_constraints(client)
    create_vector_index(client, settings)
