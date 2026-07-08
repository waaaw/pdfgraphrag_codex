from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from pypdf import PdfReader


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_pdf_pages(pdf_path: str | Path) -> dict[str, Any]:
    path = Path(pdf_path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file: {path}")

    reader = PdfReader(str(path))
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append({"page_number": index, "text": text})

    return {
        "document": {
            "filename": path.name,
            "source_path": str(path),
            "content_hash": file_sha256(path),
            "page_count": len(pages),
        },
        "pages": pages,
    }
