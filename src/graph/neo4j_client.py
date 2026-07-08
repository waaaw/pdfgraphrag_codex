from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

from src.config import Settings


class Neo4jClient:
    def __init__(self, settings: Settings):
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )

    def close(self) -> None:
        self._driver.close()

    def verify_connectivity(self) -> None:
        self._driver.verify_connectivity()

    def query(self, cypher: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        try:
            with self._driver.session() as session:
                result = session.run(cypher, parameters or {})
                return [record.data() for record in result]
        except Neo4jError as exc:
            raise RuntimeError(f"Neo4j query failed: {exc}") from exc

    def execute_write(self, cypher: str, parameters: dict[str, Any] | None = None) -> None:
        try:
            with self._driver.session() as session:
                session.execute_write(lambda tx: tx.run(cypher, parameters or {}).consume())
        except Neo4jError as exc:
            raise RuntimeError(f"Neo4j write failed: {exc}") from exc

    def execute_many(self, cypher: str, rows: Iterable[dict[str, Any]], batch_size: int = 500) -> None:
        batch: list[dict[str, Any]] = []
        for row in rows:
            batch.append(row)
            if len(batch) >= batch_size:
                self.execute_write(cypher, {"rows": batch})
                batch = []
        if batch:
            self.execute_write(cypher, {"rows": batch})

    def __enter__(self) -> "Neo4jClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
