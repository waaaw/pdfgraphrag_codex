# PDF GraphRAG QA

PDF 문서를 페이지와 청크 단위로 처리하고, Neo4j에 문서 구조와 임베딩을 저장한 뒤, Neo4j Vector Search와 LLM을 사용해 질문에 답하는 미니 GraphRAG 프로젝트입니다.

## Architecture

```text
PDF
 -> page text extraction
 -> text cleaning
 -> chunking
 -> Document/Page/Chunk nodes in Neo4j
 -> Chunk embeddings
 -> Neo4j vector index
 -> vector retrieval
 -> grounded Korean answer generation
```

1차 MVP는 `PDF -> Chunk -> Neo4j -> Embedding -> Vector Search -> QA CLI`에 집중합니다. `Entity`, `MENTIONS` 기반 그래프 확장은 `scripts/build_kg.py`로 가볍게 시작할 수 있게만 준비했습니다.

## Setup

```powershell
cd D:\develop\graphrag_codex\pdf_graphrag_qa
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`.env.example`을 참고해 `.env`를 만듭니다.

```text
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
OPENAI_API_KEY=your-api-key
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
CHAT_MODEL=gpt-4.1-mini
CHUNK_SIZE=1200
CHUNK_OVERLAP=200
VECTOR_INDEX_NAME=chunk_embedding_index
```

## Run Neo4j

```powershell
docker compose up -d
```

Neo4j Browser:

```text
http://localhost:7474
```

기본 계정:

```text
neo4j / password
```

## Create Schema

```powershell
python scripts/create_indexes.py
```

생성되는 주요 constraint:

```cypher
CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT page_id IF NOT EXISTS FOR (p:Page) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT entity_key IF NOT EXISTS FOR (e:Entity) REQUIRE e.normalized_name IS UNIQUE;
```

기본 vector index dimension은 `text-embedding-3-small`에 맞춘 `1536`입니다.

## Ingest A PDF

PDF를 `data/raw/sample.pdf`에 넣고 실행합니다.

```powershell
python scripts/extract_pdf.py data/raw/sample.pdf
python scripts/chunk_pdf.py data/processed/extracted_pages.json
python scripts/ingest_chunks.py data/processed/chunks.json
python scripts/embed_chunks.py
```

## Search

```powershell
python scripts/vector_search.py "이 문서의 핵심 내용은 무엇인가요?"
```

## Ask

```powershell
python scripts/ask.py "이 문서의 핵심 주장은 무엇인가요?"
```

답변 생성은 검색된 chunk context에 근거하며, 문서에 근거가 부족하면 부족하다고 답하도록 프롬프트를 구성했습니다.

## Optional KG Mentions

1차 MVP 이후 간단한 규칙 기반 Entity mention graph를 생성할 수 있습니다.

```powershell
python scripts/build_kg.py
```

확인 쿼리:

```cypher
MATCH (c:Chunk)-[:MENTIONS]->(e:Entity)
RETURN e.name, e.type, count(c) AS mentions
ORDER BY mentions DESC
LIMIT 20;
```

## Verification Queries

```cypher
MATCH (d:Document)
RETURN d.filename, d.page_count;
```

```cypher
MATCH (d:Document)-[:HAS_PAGE]->(p:Page)-[:HAS_CHUNK]->(c:Chunk)
RETURN d.filename, count(DISTINCT p) AS pages, count(c) AS chunks;
```

```cypher
MATCH (c:Chunk)
WHERE c.embedding IS NOT NULL
RETURN count(c) AS embedded_chunks;
```

## Tests

```powershell
pytest
```

## Notes

- OCR PDF는 텍스트 추출 결과가 비어 있을 수 있습니다. 이 경우 `ocrmypdf`나 `pytesseract` 기반 전처리를 별도 단계로 추가하세요.
- 한국어 PDF는 줄바꿈과 공백이 깨질 수 있으므로 `src/preprocessing/text_cleaner.py` 규칙을 문서에 맞춰 조정하세요.
- embedding 모델을 바꾸면 `.env`의 `EMBEDDING_DIMENSIONS`와 Neo4j vector index dimension도 같이 바꿔야 합니다.
- Cypher 값은 parameterized query로 전달합니다. label, relation type, index name처럼 parameterize하기 어려운 identifier는 allowlist 또는 안전한 식별자 검사를 거쳐야 합니다.
- `.env`와 API key는 커밋하지 마세요.
