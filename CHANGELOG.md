# Changelog

All notable changes to this project will be documented in this file.

## [v0.1.0.1] - 2026-02-10

### Fixed
- **Triple Extraction**: Fixed `TypeError` caused by Google Gemini LLM returning list output instead of string. Added type check and conversion in `TripleExtractor`.

## [v0.1.0.0] - 2026-02-07

### Added
- Initial MVP release.
- PDF ingestion pipeline (Load -> Chunk -> Extract -> Graph -> Embed).
- Hybrid retrieval (Vector + Keyword + Graph).
- Docker support for Neo4j.
