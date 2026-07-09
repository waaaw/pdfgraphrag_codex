# PDF GraphRAG QA User Manual

이 문서는 `pdf_graphrag_qa` 프로젝트를 처음 보는 사람도 목적, 용도, 실행 방법, 문제 해결 방법을 빠르게 이해할 수 있도록 정리한 사용자 매뉴얼입니다.

## 1. 프로젝트 목적

이 프로젝트는 PDF 문서를 Neo4j 기반 GraphRAG 질의응답 시스템으로 바꾸는 미니 프로젝트입니다.

일반적인 RAG는 질문과 비슷한 텍스트 조각을 벡터 검색으로 찾아 답변합니다. 이 프로젝트는 여기에 Neo4j 그래프 데이터베이스를 결합해 문서, 페이지, 청크, 엔티티 관계를 함께 다룰 수 있도록 설계되었습니다.

현재 1차 MVP의 핵심 목적은 다음입니다.

- PDF 문서를 페이지별 텍스트로 추출한다.
- 텍스트를 검색하기 좋은 청크로 나눈다.
- `Document`, `Page`, `Chunk` 노드를 Neo4j에 저장한다.
- 각 청크의 임베딩을 생성해 Neo4j vector index에 연결한다.
- 사용자의 질문과 비슷한 청크를 검색한다.
- 검색된 청크를 근거로 LLM이 한국어 답변을 생성한다.

## 2. 이 프로젝트를 쓰는 상황

이 프로젝트는 다음과 같은 경우에 적합합니다.

- PDF 보고서, 논문, 매뉴얼, 정책 문서에 대해 질문하고 싶을 때
- LangChain, Neo4j, GraphRAG의 기본 구조를 실습하고 싶을 때
- 벡터 검색과 그래프 검색을 결합하는 구조를 작게 만들어 보고 싶을 때
- 문서 기반 QA 시스템의 파이프라인을 직접 구현하고 싶을 때

현재 버전은 학습용 MVP입니다. 운영 서비스에 바로 배포하기보다는, 구조를 이해하고 기능을 확장하는 출발점으로 사용하는 것이 좋습니다.

## 3. 전체 동작 흐름

```text
PDF 파일
 -> 페이지별 텍스트 추출
 -> 텍스트 정제
 -> 청크 분할
 -> Neo4j에 Document/Page/Chunk 저장
 -> Chunk embedding 생성
 -> Neo4j vector index 검색
 -> 관련 청크를 context로 구성
 -> LLM 답변 생성
```

선택적으로 다음 단계도 사용할 수 있습니다.

```text
Chunk 텍스트
 -> 규칙 기반 Entity 추출
 -> Entity 노드 생성
 -> Chunk-[:MENTIONS]->Entity 관계 생성
```

## 4. 주요 구성 요소

### Neo4j

문서 구조와 벡터를 저장합니다.

저장되는 주요 노드:

- `Document`: PDF 파일 하나
- `Page`: PDF의 페이지
- `Chunk`: 검색 단위 텍스트 조각
- `Entity`: GraphRAG 확장용 개념 또는 키워드

주요 관계:

- `(Document)-[:HAS_PAGE]->(Page)`
- `(Page)-[:HAS_CHUNK]->(Chunk)`
- `(Chunk)-[:NEXT]->(Chunk)`
- `(Chunk)-[:MENTIONS]->(Entity)`

### OpenAI

현재 기본 설정은 OpenAI를 사용합니다.

- 임베딩 모델: `text-embedding-3-small`
- 채팅 모델: `gpt-4.1-mini`

`.env`에서 모델을 바꿀 수 있습니다.

### Python Scripts

각 단계는 `scripts` 폴더의 CLI 스크립트로 실행합니다.

## 5. 설치 방법

프로젝트 폴더로 이동합니다.

```powershell
cd D:\develop\graphrag_codex\pdf_graphrag_qa
```

가상환경을 만듭니다.

```powershell
python -m venv .venv
```

가상환경을 활성화합니다.

```powershell
.\.venv\Scripts\Activate.ps1
```

의존성을 설치합니다.

```powershell
pip install -r requirements.txt
```

## 6. 환경변수 설정

`.env.example`을 참고해 `.env` 파일을 만듭니다.

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

주의:

- `.env`는 Git에 올리지 않습니다.
- `OPENAI_API_KEY`는 반드시 본인의 키로 설정해야 합니다.
- 임베딩 모델을 바꾸면 `EMBEDDING_DIMENSIONS`도 함께 바꿔야 합니다.

## 7. Neo4j 실행

Docker Compose로 Neo4j를 실행합니다.

```powershell
docker compose up -d
```

Neo4j Browser 접속:

```text
http://localhost:7474
```

기본 접속 정보:

```text
username: neo4j
password: password
```

## 8. Neo4j 스키마 생성

constraint와 vector index를 생성합니다.

```powershell
python scripts/create_indexes.py
```

이 단계는 PDF를 넣기 전에 한 번 실행하는 것이 좋습니다.

## 9. PDF 넣기

분석할 PDF를 아래 위치에 넣습니다.

```text
data/raw/sample.pdf
```

파일명은 꼭 `sample.pdf`일 필요는 없습니다. 명령에서 실제 파일명을 지정하면 됩니다.

## 10. PDF 텍스트 추출

```powershell
python scripts/extract_pdf.py data/raw/sample.pdf
```

생성 결과:

```text
data/processed/extracted_pages.json
```

이 파일에는 PDF 문서 정보와 페이지별 텍스트가 저장됩니다.

## 11. 청크 생성

```powershell
python scripts/chunk_pdf.py data/processed/extracted_pages.json
```

생성 결과:

```text
data/processed/chunks.json
```

청크 크기와 overlap은 `.env`에서 조정합니다.

```text
CHUNK_SIZE=1200
CHUNK_OVERLAP=200
```

## 12. Neo4j에 문서 적재

```powershell
python scripts/ingest_chunks.py data/processed/chunks.json
```

적재 후 Neo4j Browser에서 확인할 수 있습니다.

```cypher
MATCH (d:Document)-[:HAS_PAGE]->(p:Page)-[:HAS_CHUNK]->(c:Chunk)
RETURN d.filename, count(DISTINCT p) AS pages, count(c) AS chunks;
```

## 13. 임베딩 생성

```powershell
python scripts/embed_chunks.py
```

이 명령은 Neo4j에 저장된 `Chunk` 중 `embedding`이 없는 노드를 찾아 OpenAI embedding을 생성하고 저장합니다.

일부만 테스트하고 싶다면:

```powershell
python scripts/embed_chunks.py --limit 10
```

## 14. 벡터 검색

```powershell
python scripts/vector_search.py "이 문서의 핵심 내용은 무엇인가요?"
```

출력에는 관련 청크의 score, page number, chunk index, text preview가 표시됩니다.

## 15. 문서 질의응답

```powershell
python scripts/ask.py "이 문서의 핵심 주장은 무엇인가요?"
```

동작 방식:

1. 질문을 embedding으로 변환합니다.
2. Neo4j vector index에서 관련 청크를 찾습니다.
3. 검색된 청크를 LLM context로 넣습니다.
4. LLM이 문서 근거 기반 한국어 답변을 생성합니다.

검색 청크 수를 바꾸고 싶다면:

```powershell
python scripts/ask.py "질문 내용" --top-k 8
```

## 16. 선택 기능: Entity Mention Graph 생성

간단한 규칙 기반 엔티티 추출을 실행할 수 있습니다.

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

현재 Entity 추출은 MVP 수준입니다. `GraphRAG`, `LangChain`, `Neo4j`, `OpenAI`, `LLM` 같은 기술 키워드와 대문자 약어를 중심으로 추출합니다.

## 17. 자주 쓰는 확인 쿼리

문서 확인:

```cypher
MATCH (d:Document)
RETURN d.filename, d.page_count, d.source_path;
```

페이지와 청크 수 확인:

```cypher
MATCH (d:Document)-[:HAS_PAGE]->(p:Page)-[:HAS_CHUNK]->(c:Chunk)
RETURN d.filename, count(DISTINCT p) AS pages, count(c) AS chunks;
```

임베딩 저장 확인:

```cypher
MATCH (c:Chunk)
RETURN count(c) AS total_chunks,
       count(c.embedding) AS embedded_chunks;
```

청크 미리보기:

```cypher
MATCH (c:Chunk)
RETURN c.page_number, c.chunk_index, left(c.text, 300) AS preview
ORDER BY c.chunk_index
LIMIT 10;
```

## 18. 테스트 실행

```powershell
python -m pytest
```

현재 테스트는 외부 Neo4j나 OpenAI 없이 실행 가능한 기본 단위 테스트입니다.

## 19. 문제 해결

### PDF에서 텍스트가 추출되지 않는 경우

PDF가 이미지 기반 OCR PDF일 수 있습니다.

해결 방법:

- OCR 처리 후 다시 시도합니다.
- `ocrmypdf`, `pytesseract` 같은 도구를 별도 전처리로 추가합니다.

### 한국어 줄바꿈이 이상한 경우

PDF 텍스트 추출 특성 때문에 문장이 줄 단위로 깨질 수 있습니다.

해결 위치:

```text
src/preprocessing/text_cleaner.py
```

문서 유형에 맞춰 줄바꿈 병합 규칙을 추가하면 됩니다.

### Vector index dimension 오류

임베딩 모델의 dimension과 Neo4j vector index dimension이 다르면 검색이 실패합니다.

확인할 값:

```text
EMBEDDING_MODEL
EMBEDDING_DIMENSIONS
```

예시:

```text
text-embedding-3-small -> 1536
text-embedding-3-large -> 3072
```

### OpenAI API 오류

확인할 항목:

- `.env`에 `OPENAI_API_KEY`가 있는지
- API key가 올바른지
- 네트워크 연결이 가능한지
- 사용 모델명이 유효한지

### Neo4j 연결 오류

확인할 항목:

- `docker compose up -d`를 실행했는지
- `http://localhost:7474` 접속이 되는지
- `.env`의 `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`가 맞는지

## 20. 현재 한계

- OCR PDF 처리는 아직 자동화되어 있지 않습니다.
- Entity/Relation 기반의 완전한 GraphRAG 검색은 아직 2차 확장 대상입니다.
- 여러 PDF를 대량 처리하는 batch 관리 기능은 단순합니다.
- 중복 문서 처리 정책은 content hash 기반의 초기 구조만 있습니다.
- 웹 UI는 없습니다. 현재는 CLI 중심입니다.

## 21. 다음 확장 아이디어

- LLM 기반 Entity/Relation extraction
- Hybrid retriever 구현
- FastAPI 서버 추가
- Streamlit 또는 React UI 추가
- OCR preprocessing pipeline 추가
- 한국어 문서용 cleaner 고도화
- QA 평가셋과 자동 평가 스크립트 추가
