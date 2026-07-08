from __future__ import annotations


ANSWER_SYSTEM_PROMPT = """You are a careful Korean GraphRAG assistant.
Answer only from the provided PDF context.
If the answer is not supported by the context, say that the document does not provide enough information.
Include page references when useful."""


def build_answer_prompt(question: str, context: str) -> str:
    return f"""PDF context:
{context}

Question:
{question}

Answer in Korean. Keep the answer grounded in the context and cite page numbers like [p. 3] when possible."""
