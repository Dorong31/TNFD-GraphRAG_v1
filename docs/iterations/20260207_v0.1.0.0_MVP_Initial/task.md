# TNFD-GraphRAG 시스템 구축 태스크

## 개요
TNFD-GraphRAG.md 아키텍처 문서 기반 Knowledge Graph RAG 시스템 구현

---

## Phase 1: MVP (Minimum Viable Product)

### 1. 프로젝트 초기화
- [x] 기본 디렉토리 구조 생성
- [x] 의존성 설정 (requirements.txt)
- [x] 환경 설정 파일 (.env.example, config.py)

### 2. 온톨로지 스키마 구현
- [x] Pydantic 모델 정의 (schemas.py)
  - [x] Organization, Location, Risk, Action, Evidence 5개 핵심 노드
  - [x] Triple 관계 정의

### 3. 데이터 파이프라인 구축
- [x] PDF 로드 모듈 (PyMuPDF4LLM)
- [x] Semantic Chunking 구현
- [x] TNFD 용어집 기반 엔티티 추출

### 4. LLM 기반 Triple 추출
- [x] Few-shot 프롬프트 설계
- [x] Triple Extraction 에이전트 구현
- [x] Evidence 노드 연결 로직

### 5. Neo4j 그래프 DB 통합
- [x] Neo4j 연결 설정
- [x] 노드/엣지 저장 로직
- [x] Vector Index 구성

### 6. Retrieval Pipeline
- [x] 하이브리드 검색 (Keyword + Vector)
- [x] Graph Traversal 로직
- [x] Context 조합 및 답변 생성

### 7. 검증 및 테스트
- [x] 단일 PDF 테스트
- [x] 질의응답 검증
- [x] 유닛 테스트 작성

---

## Phase 2: 확장 (향후)
- [ ] 전체 온톨로지 확장
- [ ] 멀티 문서 처리
- [ ] Entity Resolution

## Phase 3: 고급 기능 (향후)
- [ ] Cypher 쿼리 자동 생성
- [ ] Streamlit UI
- [ ] 그래프 시각화
