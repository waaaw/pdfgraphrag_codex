from __future__ import annotations

from src.graph.neo4j_client import Neo4jClient
from src.kg.entity_extractor import extract_entities


def build_mentions_for_existing_chunks(client: Neo4jClient, limit: int = 1000) -> int:
    rows = client.query(
        """
        MATCH (c:Chunk)
        WHERE NOT (c)-[:MENTIONS]->(:Entity)
        RETURN c.id AS id, c.text AS text
        ORDER BY c.chunk_index
        LIMIT $limit
        """,
        {"limit": limit},
    )
    mention_rows = []
    for row in rows:
        for entity in extract_entities(row["text"]):
            mention_rows.append(
                {
                    "chunk_id": row["id"],
                    "name": entity.name,
                    "normalized_name": entity.normalized_name,
                    "type": entity.type,
                }
            )

    client.execute_many(
        """
        UNWIND $rows AS row
        MATCH (c:Chunk {id: row.chunk_id})
        MERGE (e:Entity {normalized_name: row.normalized_name})
        SET e.name = row.name,
            e.type = row.type
        MERGE (c)-[:MENTIONS]->(e)
        """,
        mention_rows,
    )
    return len(mention_rows)
