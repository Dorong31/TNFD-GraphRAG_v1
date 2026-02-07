---
trigger: always_on
description: Implementation Plan과 Task 등 과업 수행계획을 수립하는 과업에서, 사용자가 승인한 최종 plan과 task의 md 파일을 기반으로 작업을 수행할 때
---

# Iterations Documents Management

## 검토 및 수행조건
- 코드 버전 업데이트 시, **커밋 전에** md 파일 아티팩트 저장

## CHAGELOG.md 업데이트
- 버전 업데이트 시, 이전 버전 대비 변경사항 추가

## markdown 파일 저장 대상
Artifacts로 생성한 md 파일로, 아래 문서를 포함
- inplementation_plan.md
- task.md
- walkthrough.md
- README.md

## 저장 경로 및 폴더명 규칙
- docs/iterations 내 신규 폴더 생성
- 신규 폴더: `yyyymmdd_{코드 버전}_{주제}`
  - 코드 버전은 4자리 버전 규칙 준수

## 단발성 테스트 파일 관리
- 디버깅이나 검증 목적의 단발성 테스트 파일(예: `debug_*.py`, `test_*.py`)은 프로젝트 루트에 남기지 않음
- docs/iterations 내 해당 버전 폴더 내에 `test` 서브폴더를 생성하여 저장
- 저장 경로: `docs/iterations/yyyymmdd_{코드 버전}_{주제}/test/`
- 관련 문서와 테스트를 같은 위치에서 관리
- 예시:
  - `debug_langsmith_metadata.py` → `docs/iterations/20260205_v0.1.3.5_History_Metadata_Fix/test/`
  - `test_metadata_update.py` → `docs/iterations/20260205_v0.1.3.5_History_Metadata_Fix/test/`
- **참고:** 프로젝트 루트의 `tests/` 폴더는 재사용 가능한 통합 테스트만 저장

## 파일 업데이트 규칙
- 동일 일자, 동일 버전에서 추가 수정이 있을 경우, 해당 폴더 내 md 파일 업데이트