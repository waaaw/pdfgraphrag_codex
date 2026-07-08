from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401

from src.config import load_settings
from src.preprocessing.chunker import build_chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Split extracted PDF pages into chunks.")
    parser.add_argument("input_json", help="Path to extracted_pages.json")
    parser.add_argument(
        "--output",
        default="data/processed/chunks.json",
        help="Output JSON path",
    )
    args = parser.parse_args()

    settings = load_settings()
    extracted = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    chunked = build_chunks(extracted, settings.chunk_size, settings.chunk_overlap)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(chunked, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {len(chunked['chunks'])} chunks to {output_path}.")


if __name__ == "__main__":
    main()
