# TNFD Knowledge Graph Construction Prompt Update Plan

## Goal Description
TNFD Recommendations, Glossary, Additional Guidance 문서 기반의 Knowledge Graph(KG) 구축을 위한 프롬프트 최적화 및 추출 로직 개선.
5가지 핵심 원칙(Evidence Grounding, Entity Normalization, Causal Chain Preservation, Atomic Decomposition, Ontology Compliance)을 적용하여 추출 정확도와 그래프 구조의 신뢰성을 향상시킴.

## User Review Required
- **System Prompt**: 4가지 핵심 원칙을 명시적으로 포함 (Evidence 연결은 시스템 자동 처리로 프롬프트 요구사항에서 제외하고 코드에서 구현).
- **Few-shot Examples**: DPSR 논리와 Atomic Decomposition을 보여주는 예시로 교체.
- **Evidence Linking**: 모든 추출된 노드를 자동으로 Evidence 노드와 `[:MENTIONS]` 관계로 연결하는 로직 추가.

## Proposed Changes

### Extraction Logic
#### [src/extraction/prompts.py](file:///c:/dev/python_pjt/TNFD-GraphRAG_v1/src/extraction/prompts.py)
- `SYSTEM_PROMPT` 업데이트: Graph Construction Prompt 내용 반영.
- `FEW_SHOT_EXAMPLES` 업데이트: DPSR 구조 및 Atomic Decomposition 반영.
- `GENERATES`, `ALTERS`, `CREATES`, `EXPOSED_TO` 관계 타입 추가.

#### [src/extraction/extractor.py](file:///c:/dev/python_pjt/TNFD-GraphRAG_v1/src/extraction/extractor.py)
- `extract` 메서드 수정: 추출된 노드들에 대해 `Evidence` 노드와의 `MENTIONS` 관계 자동 생성 로직 추가.

## Verification Plan
### Automated Tests
- `python -m src.extraction.prompts` 실행하여 프롬프트 생성 확인.
- `python -m src.extraction.extractor` 실행하여 샘플 텍스트 추출 및 JSON 파싱, Evidence 연결 확인.
