# Changelog

All notable changes to this project will be documented in this file.

## [v0.1.0.3] - 2026-02-11

### Added
- **LangSmith 연동**: `.env`에 `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`, `LANGCHAIN_ENDPOINT` 환경변수 추가
- **파이프라인 스크립트 개선** (`run_pipeline.py`):
  - 실시간 진행률 표시 (현재 청크/전체, 경과 시간, 남은 예상 시간)
  - `--start` 옵션 추가 (중단 후 재개 지원)
  - 매 청크 처리 후 중간 저장 (crash 방지)
  - 완료 시 통계 요약 출력

### Fixed
- `extractor.py`에서 불필요한 DEBUG 로그 5곳 제거

## [v0.1.0.2] - 2026-02-11

### Updated
- **KG Prompt Update**:
  - TNFD Recommendations 기반 4가지 핵심 원칙 적용 (Evidence Grounding, Entity Normalization, Causal Chain Preservation, Atomic Decomposition).
  - System Prompt 및 Few-shot Examples 전면 개편 (DPSR 구조 반영).
  - Evidence 자동 연결 로직 추가 (`[:MENTIONS]` 관계).
  - 명확한 인과 관계 표현을 위한 Ontology 관계 타입 세분화 (`GENERATES`, `ALTERS`, `CREATES` 등).

## [v0.1.0.1] - 2026-02-10

### Fixed
- **Triple Extraction**: Fixed `TypeError` caused by Google Gemini LLM returning list output instead of string. Added type check and conversion in `TripleExtractor`.

## [v0.1.0.0] - 2026-02-07

### Added
- Initial MVP release.
- PDF ingestion pipeline (Load -> Chunk -> Extract -> Graph -> Embed).
- Hybrid retrieval (Vector + Keyword + Graph).
- Docker support for Neo4j.
