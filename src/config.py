"""
TNFD-GraphRAG 시스템 설정 모듈

이 모듈은 환경 변수를 로드하고 시스템 전체에서 사용하는 설정값을 관리합니다.
.env 파일에서 API 키, 데이터베이스 연결 정보, 모델 설정 등을 읽어옵니다.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ============ 기본 경로 설정 ============
# 프로젝트 루트 디렉토리를 기준으로 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PDF_DIR = DATA_DIR / "pdfs"
GLOSSARY_DIR = DATA_DIR / "glossary"

# ============ 환경 변수 로드 ============
# .env 파일이 있으면 로드 (없어도 에러 발생하지 않음)
load_dotenv(PROJECT_ROOT / ".env")

# ============ API 키 ============
# Google Gemini API 키 (LLM용)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# OpenAI API 키 (사용하지 않음, 호환성 유지용)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ============ Neo4j 데이터베이스 설정 ============
# Neo4j 연결 URI (로컬 또는 AuraDB)
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")

# Neo4j 인증 정보
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

# ============ 모델 설정 ============
# LLM 모델명 (Gemini)
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")

# 임베딩 모델명 (Google Gemini Embedding)
# gemini-embedding-001은 768차원 출력 지원
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")

# 임베딩 차원 수 (gemini-embedding-001: 768차원으로 통일)
EMBEDDING_DIMENSION = 768

# ============ 그래프 설정 ============
# Graph Traversal 깊이 (몇 hop까지 탐색할지)
GRAPH_TRAVERSAL_DEPTH = int(os.getenv("GRAPH_TRAVERSAL_DEPTH", "2"))

# 검색 결과 상위 K개
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))

# ============ 청킹 설정 ============
# 청크 크기 (문자 수 기준)
CHUNK_SIZE = 1000

# 청크 간 오버랩 (문자 수 기준)
CHUNK_OVERLAP = 200

# ============ 노드 타입 정의 (Phase 1 MVP) ============
# Phase 1에서 사용하는 5개 핵심 노드 타입
NODE_TYPES = [
    "Organization",  # 분석 대상 기업/조직
    "Location",      # 사업장 또는 자산의 위치
    "Risk",          # 물리적/이행 리스크
    "Action",        # 완화 조치 및 전략
    "Evidence",      # 정보 출처 (텍스트 청크)
]

# ============ 관계 타입 정의 (Phase 1 MVP) ============
# Phase 1에서 사용하는 관계 타입
RELATIONSHIP_TYPES = [
    "OPERATES_IN",   # Organization -> Location
    "HAS_RISK",      # Organization -> Risk
    "IMPLEMENTS",    # Organization -> Action
    "MITIGATES",     # Action -> Risk
    "SUPPORTS",      # Evidence -> Action/Risk
    "MENTIONS",      # Evidence -> any Node
    "LOCATED_IN",    # nested Location
]


def validate_config() -> dict[str, bool]:
    """
    설정 유효성을 검사하고 결과를 반환합니다.
    
    Returns:
        dict: 각 설정 항목의 유효성 여부
    """
    return {
        "google_api_key": bool(GOOGLE_API_KEY),
        "openai_api_key": bool(OPENAI_API_KEY),
        "neo4j_password": bool(NEO4J_PASSWORD),
        "pdf_dir_exists": PDF_DIR.exists(),
        "glossary_dir_exists": GLOSSARY_DIR.exists(),
    }


if __name__ == "__main__":
    # 설정 검증 테스트
    print("=== TNFD-GraphRAG 설정 검증 ===")
    validation = validate_config()
    for key, valid in validation.items():
        status = "✓" if valid else "✗"
        print(f"  {status} {key}: {'설정됨' if valid else '미설정'}")
