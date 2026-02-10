# TNFD-GraphRAG

**Nature-related Financial Disclosure Analysis System based on Knowledge Graph**

TNFD(자연 관련 재무 정보 공개) 프레임워크를 기반으로 기업의 지속가능성 보고서를 분석하고, Knowledge Graph와 RAG를 결합한 질의응답 시스템입니다.

## 🎯 주요 기능

- **PDF 문서 분석**: 지속가능성 보고서에서 TNFD 관련 정보 자동 추출
- **Knowledge Graph 구축**: 리스크, 조치, 위치 등 엔티티 간 관계를 그래프로 시각화
- **하이브리드 검색**: Vector 검색 + Keyword 검색 + Graph Traversal
- **설명 가능한 AI**: 답변과 함께 출처(Evidence) 및 근거 경로 제시

## 📁 프로젝트 구조

```
TNFD-GraphRAG_v1/
├── src/
│   ├── config.py              # 환경 설정
│   ├── schemas.py             # Pydantic 노드/관계 스키마
│   ├── data_pipeline/         # PDF 로드 및 청킹
│   ├── extraction/            # LLM 기반 Triple 추출
│   ├── graph/                 # Neo4j 통합
│   └── retrieval/             # 하이브리드 검색 및 답변 생성
├── tests/                     # 유닛 테스트
├── scripts/                   # 실행 스크립트
├── data/                      # PDF 및 용어집 데이터
├── requirements.txt
└── .env.example
```

## 🚀 빠른 시작

### 1. 설치

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 설정
cp .env.example .env
# .env 파일을 열어 Google API 키와 Neo4j 정보 입력
```

### 2. Neo4j Docker 실행

```bash
docker run -d \
  --name neo4j-tnfd \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  -e NEO4J_PLUGINS='["apoc"]' \
  -v neo4j_data:/data \
  neo4j:5.26-community
```

웹 브라우저에서 `http://localhost:7474`로 접속하여 Neo4j Browser 확인

### 3. 환경 변수 설정 (.env)

```env
GOOGLE_API_KEY=your-google-api-key
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

### 4. PDF 문서로 Knowledge Graph 구축

```bash
python scripts/run_pipeline.py --pdf "data/pdfs/207940_삼성바이오로직스_2025_KR.pdf"
```

### 5. 질의응답

```bash
python scripts/run_pipeline.py --query "이 기업의 주요 물리적 리스크는 무엇입니까?"
```

## 📊 온톨로지 스키마 (Phase 1)

### 노드 타입
| Type | 설명 |
|------|------|
| **Organization** | 분석 대상 기업/조직 |
| **Location** | 사업장 위치 |
| **Risk** | 물리적/이행 리스크 |
| **Action** | 완화 조치 및 전략 |
| **Evidence** | 정보 출처 (텍스트 청크) |

### 관계 타입
- `OPERATES_IN`: Organization → Location
- `HAS_RISK`: Organization → Risk
- `IMPLEMENTS`: Organization → Action
- `MITIGATES`: Action → Risk
- `SUPPORTS`: Evidence → Node

## 🧪 테스트

```bash
pytest tests/ -v
```

## 📖 기술 스택

- **LLM**: Google Gemini (gemini-3-flash-preview)
- **Embedding**: Google Gemini Embedding (gemini-embedding-001, 768차원)
- **Graph DB**: Neo4j (Docker Community Edition)
- **PDF 처리**: PyMuPDF4LLM
- **Orchestration**: LangChain

## 📄 라이선스

MIT License
