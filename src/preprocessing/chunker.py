from __future__ import annotations

import hashlib
import json
from typing import Any

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:  # pragma: no cover
    RecursiveCharacterTextSplitter = None

from src.preprocessing.text_cleaner import clean_text


KOREAN_FRIENDLY_SEPARATORS = ["\n\n", "\n", "다.", ".", "。", " ", ""]


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_json_hash(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return stable_hash(encoded)


def make_document_id(document: dict[str, Any]) -> str:
    return "doc_" + stable_hash(document["content_hash"])[:16]


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    if not text.strip():
        return []
    if RecursiveCharacterTextSplitter is None:
        step = max(chunk_size - chunk_overlap, 1)
        return [text[i : i + chunk_size] for i in range(0, len(text), step)]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=KOREAN_FRIENDLY_SEPARATORS,
    )
    return splitter.split_text(text)


def build_chunks(extracted: dict[str, Any], chunk_size: int, chunk_overlap: int) -> dict[str, Any]:
    document = dict(extracted["document"])
    document_id = make_document_id(document)
    document["id"] = document_id

    chunks: list[dict[str, Any]] = []
    global_index = 0
    previous_chunk_id: str | None = None

    for page in extracted["pages"]:
        page_number = int(page["page_number"])
        cleaned = clean_text(page.get("text", ""))
        for page_chunk_index, chunk_text in enumerate(split_text(cleaned, chunk_size, chunk_overlap)):
            chunk_hash = stable_hash(f"{document_id}:{page_number}:{page_chunk_index}:{chunk_text}")
            chunk_id = "chunk_" + chunk_hash[:24]
            chunk = {
                "id": chunk_id,
                "document_id": document_id,
                "page_number": page_number,
                "chunk_index": global_index,
                "page_chunk_index": page_chunk_index,
                "text": chunk_text,
                "content_hash": stable_hash(chunk_text),
                "char_count": len(chunk_text),
                "previous_chunk_id": previous_chunk_id,
            }
            chunks.append(chunk)
            previous_chunk_id = chunk_id
            global_index += 1

    return {"document": document, "chunks": chunks}
