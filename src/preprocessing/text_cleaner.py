from __future__ import annotations

import re


_MULTI_SPACE = re.compile(r"[ \t]+")
_MULTI_NEWLINE = re.compile(r"\n{3,}")
_BROKEN_HYPHEN = re.compile(r"(\w)-\n(\w)")


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _BROKEN_HYPHEN.sub(r"\1\2", text)
    lines = [_MULTI_SPACE.sub(" ", line).strip() for line in text.split("\n")]
    text = "\n".join(line for line in lines if line)
    text = _MULTI_NEWLINE.sub("\n\n", text)
    return text.strip()


def text_preview(text: str, limit: int = 240) -> str:
    compact = _MULTI_SPACE.sub(" ", text.replace("\n", " ")).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."
