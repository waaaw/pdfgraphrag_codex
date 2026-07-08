from src.preprocessing.chunker import build_chunks, stable_hash


def test_stable_hash_is_deterministic() -> None:
    assert stable_hash("GraphRAG") == stable_hash("GraphRAG")


def test_build_chunks_preserves_page_and_document_metadata() -> None:
    extracted = {
        "document": {
            "filename": "sample.pdf",
            "source_path": "data/raw/sample.pdf",
            "content_hash": "abc123",
            "page_count": 1,
        },
        "pages": [
            {
                "page_number": 1,
                "text": "LangChain and Neo4j can be used for GraphRAG. " * 20,
            }
        ],
    }

    result = build_chunks(extracted, chunk_size=120, chunk_overlap=20)

    assert result["document"]["id"].startswith("doc_")
    assert result["chunks"]
    assert all(chunk["page_number"] == 1 for chunk in result["chunks"])
    assert result["chunks"][0]["chunk_index"] == 0
    assert result["chunks"][0]["previous_chunk_id"] is None
