from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401

from src.loaders.pdf_loader import load_pdf_pages
from src.preprocessing.text_cleaner import clean_text


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract page text from a PDF.")
    parser.add_argument("pdf_path", help="Path to a PDF file")
    parser.add_argument(
        "--output",
        default="data/processed/extracted_pages.json",
        help="Output JSON path",
    )
    args = parser.parse_args()

    extracted = load_pdf_pages(args.pdf_path)
    for page in extracted["pages"]:
        page["text"] = clean_text(page["text"])

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(extracted, ensure_ascii=False, indent=2), encoding="utf-8")

    page_count = len(extracted["pages"])
    print(f"Extracted {page_count} pages to {output_path}.")


if __name__ == "__main__":
    main()
