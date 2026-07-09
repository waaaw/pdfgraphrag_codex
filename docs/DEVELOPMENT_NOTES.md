# PDF GraphRAG QA Development Notes

이 문서는 프로젝트 개발 진행 상황, 설계 결정, 구현된 파일의 역할, 남은 작업을 기록하는 개발노트입니다.

## 1. 개발 기준일

- 최초 계획 수립: 2026-07-08
- 초기 MVP 스캐폴딩 및 구현: 2026-07-08
- 매뉴얼 및 개발노트 작성: 2026-07-09

## 2. 현재 개발 목표

첫 번째 목표는 PDF GraphRAG의 1차 MVP를 완성하는 것입니다.

1차 MVP의 성공 기준:

- PDF 텍스트를 페이지 단위로 추출할 수 있다.
- 텍스트를 청크로 나눌 수 있다.
- Neo4j에 `Document`, `Page`, `Chunk`를 저장할 수 있다.
- `Chunk.embedding`을 저장할 수 있다.
- Neo4j vector index로 관련 청크를 검색할 수 있다.
- 검색 결과를 근거로 LLM 답변을 생성할 수 있다.

2차 목표:

- `Entity` 노드와 `MENTIONS` 관계를 활용한다.
- Vector retrieval과 graph retrieval을 결합한다.
- LLM 기반 relation extraction을 추가한다.

## 3. 구현된 범위

현재 구현된 범위:

- Python 프로젝트 구조
- Docker Compose 기반 Neo4j 실행 설정
- 환경변수 로딩
- Neo4j 연결 client
- Neo4j constraint 및 vector index 생성
- PDF 페이지 텍스트 추출
- 텍스트 정제
- 청킹
- Document/Page/Chunk Neo4j 적재
- Chunk embedding 생성 및 저장
- Neo4j vector search
- 검색 결과 기반 QA
- 규칙 기반 Entity mention graph의 기초
- 기본 단위 테스트
- 사용자 README
- 사용자 매뉴얼
- 개발노트

아직 구현되지 않았거나 제한적인 범위:

- OCR PDF 자동 처리
- LLM 기반 Entity/Relation extraction
- Hybrid graph retriever
- FastAPI 또는 웹 UI
- 운영용 에러 처리와 모니터링
- 대용량 PDF batch 처리 최적화

## 4. 주요 설계 결정

### 4.1 1차 MVP는 Vector QA 중심

처음부터 Entity/Relation 추출까지 구현하면 실패 지점이 많아집니다. 그래서 1차 MVP는 아래 흐름에 집중했습니다.

```text
PDF -> Chunk -> Neo4j -> Embedding -> Vector Search -> QA
```

이후 graph 기능을 단계적으로 붙일 수 있게 `src/kg` 구조만 미리 준비했습니다.

### 4.2 Neo4j 적재는 직접 Cypher 사용

LangChain의 고수준 abstraction을 바로 사용하지 않고, Neo4j Python driver와 직접 Cypher를 사용했습니다.

이유:

- 어떤 노드와 관계가 생성되는지 명확히 볼 수 있음
- 디버깅이 쉬움
- Cypher injection 방어를 직접 확인할 수 있음
- 추후 LangChain retriever로 바꾸더라도 데이터 모델을 유지할 수 있음

### 4.3 모든 사용자 값은 parameterized query 사용

Cypher injection을 피하기 위해 값은 모두 parameter로 전달합니다.

단, vector index name처럼 Cypher identifier가 필요한 경우에는 parameterize하기 어렵기 때문에 `safe_identifier`로 안전한 문자만 허용합니다.

### 4.4 content hash 기반 중복 방지 준비

`Document`와 `Chunk`에는 `content_hash`를 둡니다.

현재는 기본적인 중복 방지와 추적을 위한 값이며, 추후 다음 정책으로 확장할 수 있습니다.

- 같은 PDF 재적재 시 skip
- 같은 청크 embedding 재사용
- 문서 버전 관리
- incremental ingest

### 4.5 스크립트 기반 CLI 우선

웹 UI나 API보다 CLI를 먼저 구현했습니다.

이유:

- 단계별 디버깅이 쉬움
- Neo4j 상태 확인과 연결하기 좋음
- 학습용 프로젝트에서 파이프라인 이해가 쉬움

## 5. 파일별 역할

### Root files

`README.md`

- 빠른 시작과 핵심 실행 명령을 담은 기본 문서입니다.

`.env.example`

- 필요한 환경변수 예시입니다.
- 실제 `.env`는 Git에 올리지 않습니다.

`.gitignore`

- `.env`, `.venv`, cache, processed data를 제외합니다.

`docker-compose.yml`

- Neo4j 5.x community 컨테이너 실행 설정입니다.

`requirements.txt`

- Python 의존성 목록입니다.

### Config

`src/config.py`

- `.env`를 읽어 `Settings` dataclass로 반환합니다.
- Neo4j, OpenAI, chunking, vector index 설정을 관리합니다.

### PDF Loading

`src/loaders/pdf_loader.py`

- `pypdf`로 PDF를 읽습니다.
- 페이지별 텍스트를 추출합니다.
- PDF 파일의 SHA-256 hash를 계산합니다.

`scripts/extract_pdf.py`

- PDF 파일을 받아 `data/processed/extracted_pages.json`을 생성합니다.

### Preprocessing

`src/preprocessing/text_cleaner.py`

- 공백, 줄바꿈, 하이픈 줄바꿈을 정리합니다.
- 출력 preview를 생성합니다.

`src/preprocessing/chunker.py`

- LangChain `RecursiveCharacterTextSplitter`를 사용해 청크를 만듭니다.
- LangChain이 없는 환경에서는 간단한 fallback splitter를 사용합니다.
- `document_id`, `chunk_id`, `content_hash`를 생성합니다.

`scripts/chunk_pdf.py`

- `extracted_pages.json`을 읽어 `chunks.json`을 생성합니다.

### Neo4j Graph

`src/graph/neo4j_client.py`

- Neo4j driver wrapper입니다.
- query, write, batch write helper를 제공합니다.

`src/graph/schema.py`

- constraint와 vector index를 생성합니다.
- vector index name은 안전한 identifier인지 검사합니다.

`src/graph/ingest.py`

- `Document`, `Page`, `Chunk` 노드와 관계를 생성합니다.
- `HAS_PAGE`, `HAS_CHUNK`, `NEXT` 관계를 만듭니다.

`scripts/create_indexes.py`

- Neo4j schema를 생성하는 CLI입니다.

`scripts/ingest_chunks.py`

- `chunks.json`을 Neo4j에 적재하는 CLI입니다.

### Embeddings

`src/embeddings/embedding_client.py`

- OpenAI embedding API wrapper입니다.
- batch embedding과 query embedding을 제공합니다.

`scripts/embed_chunks.py`

- Neo4j에서 embedding이 없는 Chunk를 찾아 embedding을 생성하고 저장합니다.

### Retrieval

`src/retrieval/vector_retriever.py`

- 질문을 embedding으로 바꾸고 Neo4j vector search를 실행합니다.
- 검색 결과를 `RetrievedChunk` dataclass로 반환합니다.

`scripts/vector_search.py`

- 질문을 입력받아 관련 청크를 출력하는 CLI입니다.

### QA

`src/qa/prompts.py`

- 답변 생성용 system prompt와 user prompt builder를 담습니다.

`src/qa/answer_generator.py`

- 검색된 chunk context를 LLM에 전달해 한국어 답변을 생성합니다.

`scripts/ask.py`

- 검색과 답변 생성을 한 번에 수행하는 CLI입니다.

### KG Extension

`src/kg/entity_extractor.py`

- 규칙 기반 Entity 추출기입니다.
- 기술 키워드와 대문자 약어를 추출합니다.

`src/kg/graph_builder.py`

- 기존 Chunk를 읽어 Entity 노드와 `MENTIONS` 관계를 만듭니다.

`scripts/build_kg.py`

- Entity mention graph를 생성하는 CLI입니다.

### Tests

`tests/test_text_cleaner.py`

- 텍스트 정제와 preview를 검증합니다.

`tests/test_chunker.py`

- hash 안정성과 chunk metadata 유지를 검증합니다.

## 6. 현재 검증 상태

완료된 검증:

```powershell
python -m compileall src scripts tests
```

결과:

- 전체 Python 파일 문법 검사 통과

아직 제한된 검증:

- `pytest`는 당시 로컬 환경에 설치되어 있지 않아 실행하지 못했습니다.
- Neo4j container 실행 검증은 아직 수행하지 않았습니다.
- OpenAI API 호출 검증은 아직 수행하지 않았습니다.
- 실제 PDF end-to-end ingest 검증은 아직 수행하지 않았습니다.

다음 검증 권장 순서:

```powershell
pip install -r requirements.txt
python -m pytest
docker compose up -d
python scripts/create_indexes.py
python scripts/extract_pdf.py data/raw/sample.pdf
python scripts/chunk_pdf.py data/processed/extracted_pages.json
python scripts/ingest_chunks.py data/processed/chunks.json
python scripts/embed_chunks.py --limit 5
python scripts/vector_search.py "이 문서의 핵심 내용은 무엇인가요?"
```

## 7. 데이터 모델

### Document

```text
id
filename
source_path
content_hash
page_count
created_at
updated_at
```

### Page

```text
id
document_id
page_number
text_preview
```

### Chunk

```text
id
document_id
page_number
chunk_index
page_chunk_index
text
content_hash
char_count
embedding
```

### Entity

```text
name
normalized_name
type
```

## 8. Cypher 설계 메모

문서 적재:

```cypher
MERGE (d:Document {id: $id})
SET d.filename = $filename,
    d.source_path = $source_path,
    d.content_hash = $content_hash,
    d.page_count = $page_count
```

벡터 검색:

```cypher
CALL db.index.vector.queryNodes($index_name, $top_k, $embedding)
YIELD node, score
RETURN node.id, node.text, node.page_number, score
ORDER BY score DESC
```

Entity mention graph:

```cypher
MATCH (c:Chunk {id: row.chunk_id})
MERGE (e:Entity {normalized_name: row.normalized_name})
MERGE (c)-[:MENTIONS]->(e)
```

## 9. 비용 관리 메모

비용이 발생하는 단계:

- `scripts/embed_chunks.py`
- `scripts/ask.py`

비용 절감 방법:

- 처음에는 작은 PDF로 테스트합니다.
- `embed_chunks.py --limit 5`처럼 일부 청크만 임베딩합니다.
- `ask.py --top-k 3`처럼 context 청크 수를 줄입니다.
- 문서 재처리 시 embedding이 있는 Chunk는 건너뜁니다.

## 10. 보안 메모

- `.env`는 Git에 포함하지 않습니다.
- OpenAI API key를 코드나 README에 직접 쓰지 않습니다.
- Cypher는 parameterized query를 사용합니다.
- 사용자가 입력한 문자열로 label, relationship type, index name을 직접 만들지 않습니다.
- vector index name은 `safe_identifier` 검사를 통과해야 합니다.

## 11. 다음 작업 목록

우선순위 높은 작업:

1. 의존성 설치 후 `pytest` 실행
2. Neo4j Docker 실행 검증
3. 샘플 PDF 추가
4. PDF extraction 결과 확인
5. chunk 품질 확인
6. Neo4j ingest 확인
7. embedding 일부 생성 테스트
8. vector search 결과 확인
9. QA 답변 품질 확인

기능 확장 작업:

1. OCR PDF preprocessing 추가
2. 한국어 PDF cleaner 개선
3. LLM 기반 Entity extraction 추가
4. LLM 기반 Relation extraction 추가
5. GraphRetriever 구현
6. HybridRetriever 구현
7. FastAPI endpoint 추가
8. Streamlit 또는 React UI 추가
9. QA 평가 질문셋 추가
10. 비용/토큰 사용량 logging 추가

## 12. 알려진 리스크

### PDF 추출 품질

PDF 포맷에 따라 텍스트 추출 품질이 크게 달라집니다. OCR PDF는 현재 자동 처리하지 않습니다.

### 한국어 문서 처리

한국어 PDF는 줄바꿈, 띄어쓰기, 표 추출에서 품질 문제가 생길 수 있습니다.

### Vector index dimension

임베딩 모델을 바꾸면 Neo4j vector index를 다시 만들어야 할 수 있습니다.

### API 비용

큰 PDF를 한 번에 embedding하면 비용이 늘어날 수 있습니다.

### GraphRAG 품질

현재 `Entity` 추출은 규칙 기반 MVP입니다. 진짜 GraphRAG 품질을 내려면 relation extraction과 graph traversal 전략이 더 필요합니다.

## 13. 커밋 기록

초기 커밋:

```text
3485dbb Initial PDF GraphRAG QA MVP
```

초기 커밋에 포함된 내용:

- 프로젝트 스캐폴딩
- Neo4j 설정
- PDF 처리 파이프라인
- embedding/vector search/QA CLI
- KG 확장 스텁
- 기본 테스트
- README
