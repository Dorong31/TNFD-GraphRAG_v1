# TNFD-GraphRAG 시스템 구축 완료

## 구현 완료 항목

| 구성요소 | 설명 |
|----------|------|
| **가상환경** | uv (Python 3.11) |
| **임베딩** | `gemini-embedding-001` (768차원) |
| **LLM** | `gemini-2.0-flash` |
| **그래프 DB** | Neo4j Docker Community |
| **테스트 PDF** | 삼성바이오로직스 2025 지속가능성 보고서 |

---

## 프로젝트 구조

```
src/
├── config.py              # 환경 설정 (768차원 임베딩)
├── schemas.py             # 5개 핵심 노드 스키마
├── data_pipeline/         # PDF 로더, 청킹, 용어집
├── extraction/            # LLM Triple 추출
├── graph/                 # Neo4j + Vector Store
└── retrieval/             # 하이브리드 검색 + 답변 생성
```

---

## 설정 변경 사항

- `gemini-embedding-001` 768차원으로 통일
- `google-genai` 패키지 사용 (최신 API)
- Python 3.11~3.13 호환

---

## 다음 단계

### 1. 환경 변수 설정
```bash
cp .env.example .env
# GOOGLE_API_KEY, NEO4J_PASSWORD 입력
```

### 2. Neo4j Docker 실행
```bash
docker run -d --name neo4j-tnfd \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -v neo4j_data:/data \
  neo4j:5.26-community
```

### 3. PDF 분석 실행
```bash
uv run python scripts/run_pipeline.py --pdf "data/pdfs/207940_삼성바이오로직스_2025_KR.pdf"
```

### 4. 질의응답
```bash
uv run python scripts/run_pipeline.py --query "이 기업의 주요 물리적 리스크는?"
```
