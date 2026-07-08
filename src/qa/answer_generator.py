from __future__ import annotations

from openai import OpenAI

from src.config import Settings
from src.qa.prompts import ANSWER_SYSTEM_PROMPT, build_answer_prompt
from src.retrieval.vector_retriever import RetrievedChunk


def format_context(chunks: list[RetrievedChunk]) -> str:
    blocks = []
    for chunk in chunks:
        blocks.append(
            f"[page {chunk.page_number}, chunk {chunk.chunk_index}, score {chunk.score:.4f}]\n{chunk.text}"
        )
    return "\n\n---\n\n".join(blocks)


class AnswerGenerator:
    def __init__(self, settings: Settings):
        if not settings.openai_api_key or settings.openai_api_key == "your-api-key":
            raise ValueError("OPENAI_API_KEY is required for answer generation.")
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.chat_model

    def answer(self, question: str, chunks: list[RetrievedChunk]) -> str:
        context = format_context(chunks)
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": ANSWER_SYSTEM_PROMPT},
                {"role": "user", "content": build_answer_prompt(question, context)},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""
