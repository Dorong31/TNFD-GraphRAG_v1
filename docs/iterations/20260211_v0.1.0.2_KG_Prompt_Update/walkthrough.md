# Walkthrough: TNFD Knowledge Graph Extraction Prompt Update

이 문서는 TNFD Recommendations 및 공식 문서 기반의 Knowledge Graph 구축을 위한 프롬프트와 추출 로직의 업데이트 내용을 설명합니다.
버전: `v0.1.0.2` (2026.02.11)

## 개요
사용자가 정의한 5가지 핵심 원칙에 따라 TNFD 관련 정보를 구조적으로 추출하기 위해 시스템 프롬프트(System Prompt)와 Few-shot 예시를 전면 개편하고, 추출된 정보의 근거(Evidence)를 명확히 하기 위한 자동 연결 로직을 추가했습니다.

## 주요 변경 사항

### 1. 프롬프트 업데이트 (System Prompt & Few-shot)
- **파일**: [`src/extraction/prompts.py`](file:///c:/dev/python_pjt/TNFD-GraphRAG_v1/src/extraction/prompts.py)
- **내용**:
  - **Evidence Grounding**: 모든 사실은 원문에 근거해야 함을 명시. (연결은 후처리로 구현)
  - **Entity Normalization**: TNFD 표준 용어 사용 유도.
  - **Causal Chain Preservation**: DPSR(Driver-Pressure-State-Response) 인과 관계 구조 도입. (`GENERATES`, `ALTERS`, `CREATES` 등 신규 관계 추가)
  - **Atomic Decomposition**: 복합 문장을 단일 Triple로 분해하는 원칙 및 예시 추가.

### 2. Evidence 자동 연결 로직 추가
- **파일**: [`src/extraction/extractor.py`](file:///c:/dev/python_pjt/TNFD-GraphRAG_v1/src/extraction/extractor.py)
- **내용**:
  - LLM이 추출한 모든 노드(Organization, Location, Risk, Action)에 대해, 해당 정보의 출처가 되는 `Evidence` 노드와 `[:MENTIONS]` 관계를 자동으로 생성하는 로직 추가.
  - 이를 통해 LLM 토큰 낭비를 줄이면서도 확실한 근거 추적(Citation) 기능 보장.

## 검증 (Verification)
- `python -m src.extraction.prompts`: 업데이트된 프롬프트가 의도대로 생성됨을 확인.
- `python -m src.extraction.extractor`: 샘플 텍스트에 대해 DPSR 구조의 Triple이 추출되고, Evidence 노드와 연결됨을 확인(코드 레벨).

## 실행 방법
```bash
# 프롬프트 확인
python -m src.extraction.prompts

# 추출 로직 테스트 (GOOGLE_API_KEY 설정 필요)
python -m src.extraction.extractor
```
