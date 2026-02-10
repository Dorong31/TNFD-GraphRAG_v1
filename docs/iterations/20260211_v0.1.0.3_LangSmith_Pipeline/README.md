# v0.1.0.3 - LangSmith 연동 및 파이프라인 개선

## 변경 개요

LangSmith Observability 연동을 위한 환경변수 설정 추가 및 Triple 추출 파이프라인 스크립트 전면 개선.

## 주요 변경사항

### 1. LangSmith 연동 (`LANGCHAIN_TRACING_V2`)
- `.env` / `.env.example`에 LangSmith 환경변수 4종 추가
- `langsmith 0.5.0` (기설치) 패키지를 활용한 자동 트레이싱

### 2. 파이프라인 스크립트 개선 (`run_pipeline.py`)
- 실시간 진행률 표시 (현재/전체 청크, 소요시간, ETA)
- `--start` 옵션: 중단 후 재개 지원
- 매 청크당 중간 저장: crash 시에도 결과 보존
- 완료 통계 출력 (총 노드/관계, 빈 청크, 평균 시간)

### 3. DEBUG 로그 정리 (`extractor.py`)
- 프로덕션 코드에서 불필요한 DEBUG print 5곳 제거

## 테스트 결과

삼성바이오로직스 PDF (224페이지, 429청크) 중 본문 시작 3개 청크 테스트:

| 지표 | 값 |
|------|-----|
| 총 노드 | 16 |
| 총 관계 | 25 |
| 빈 청크 | 0/3 |
| 평균 소요 | 12.3초/청크 |
| 총 소요 | 0.6분 |

추출된 엔티티: Organization(Samsung Biologics), Location(Supply Chain), Action(Eco-friendly Operations, PwC TIMM 등), Risk(Environmental/Social/Economic Impact), Evidence(원문 텍스트)
