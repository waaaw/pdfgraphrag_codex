from __future__ import annotations

from openai import OpenAI

from src.config import Settings


class EmbeddingClient:
    def __init__(self, settings: Settings):
        if not settings.openai_api_key or settings.openai_api_key == "your-api-key":
            raise ValueError("OPENAI_API_KEY is required for embedding generation.")
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.embedding_model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]
