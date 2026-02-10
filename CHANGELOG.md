# Changelog

All notable changes to this project will be documented in this file.

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
