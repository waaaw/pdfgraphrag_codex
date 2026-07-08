from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.graph.neo4j_client import Neo4jClient
from src.preprocessing.text_cleaner import text_preview


def ingest_document_chunks(client: Neo4jClient, payload: dict[str, Any]) -> None:
    document = dict(payload["document"])
    document["created_at"] = datetime.now(timezone.utc).isoformat()
    chunks = payload["chunks"]

    pages = {}
    for chunk in chunks:
        page_number = int(chunk["page_number"])
        page_id = f"{document['id']}_page_{page_number}"
        pages.setdefault(
            page_number,
            {
                "id": page_id,
                "document_id": document["id"],
                "page_number": page_number,
                "text_preview": text_preview(chunk["text"]),
            },
        )

    client.execute_write(
        """
        MERGE (d:Document {id: $id})
        SET d.filename = $filename,
            d.source_path = $source_path,
            d.content_hash = $content_hash,
            d.page_count = $page_count,
            d.created_at = coalesce(d.created_at, $created_at),
            d.updated_at = $created_at
        """,
        document,
    )

    client.execute_many(
        """
        UNWIND $rows AS row
        MATCH (d:Document {id: row.document_id})
        MERGE (p:Page {id: row.id})
        SET p.document_id = row.document_id,
            p.page_number = row.page_number,
            p.text_preview = row.text_preview
        MERGE (d)-[:HAS_PAGE]->(p)
        """,
        pages.values(),
    )

    client.execute_many(
        """
        UNWIND $rows AS row
        MATCH (p:Page {id: row.document_id + '_page_' + toString(row.page_number)})
        MERGE (c:Chunk {id: row.id})
        SET c.document_id = row.document_id,
            c.page_number = row.page_number,
            c.chunk_index = row.chunk_index,
            c.page_chunk_index = row.page_chunk_index,
            c.text = row.text,
            c.content_hash = row.content_hash,
            c.char_count = row.char_count
        MERGE (p)-[:HAS_CHUNK]->(c)
        """,
        chunks,
    )

    next_rows = [
        {"previous_chunk_id": chunk["previous_chunk_id"], "chunk_id": chunk["id"]}
        for chunk in chunks
        if chunk.get("previous_chunk_id")
    ]
    client.execute_many(
        """
        UNWIND $rows AS row
        MATCH (prev:Chunk {id: row.previous_chunk_id})
        MATCH (curr:Chunk {id: row.chunk_id})
        MERGE (prev)-[:NEXT]->(curr)
        """,
        next_rows,
    )
