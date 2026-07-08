from __future__ import annotations

import re
from dataclasses import dataclass


TECH_KEYWORDS = {
    "GraphRAG",
    "RAG",
    "LangChain",
    "Neo4j",
    "OpenAI",
    "LLM",
    "PDF",
    "Embedding",
    "Vector",
    "Cypher",
}


@dataclass(frozen=True)
class Entity:
    name: str
    normalized_name: str
    type: str = "Concept"


def normalize_entity_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip().lower()


def extract_entities(text: str) -> list[Entity]:
    found: dict[str, Entity] = {}
    for keyword in TECH_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", text, flags=re.IGNORECASE):
            normalized = normalize_entity_name(keyword)
            found[normalized] = Entity(name=keyword, normalized_name=normalized)

    for acronym in re.findall(r"\b[A-Z][A-Z0-9]{1,}\b", text):
        normalized = normalize_entity_name(acronym)
        found.setdefault(normalized, Entity(name=acronym, normalized_name=normalized, type="Acronym"))

    return sorted(found.values(), key=lambda entity: entity.normalized_name)
