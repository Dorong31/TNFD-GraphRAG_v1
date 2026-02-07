"""
TNFD 용어집 (Glossary) 모듈

TNFD 프레임워크의 핵심 용어를 정의하고, 
텍스트에서 전문 용어를 식별하는 기능을 제공합니다.
"""

from typing import Optional

# ============ TNFD 핵심 용어 정의 ============
# 출처: TNFD 공식 가이드라인 및 Glossary

TNFD_GLOSSARY = {
    # ===== LEAP 프레임워크 관련 =====
    "LEAP": {
        "definition": "Locate, Evaluate, Assess, Prepare - TNFD의 위험 및 기회 평가 프레임워크",
        "category": "Framework",
    },
    "Locate": {
        "definition": "조직의 활동과 자연과의 접점(nature interface)이 있는 위치 식별",
        "category": "Framework",
    },
    "Evaluate": {
        "definition": "자연에 대한 의존성(dependencies)과 영향(impacts) 평가",
        "category": "Framework",
    },
    "Assess": {
        "definition": "자연 관련 위험과 기회 평가",
        "category": "Framework",
    },
    "Prepare": {
        "definition": "대응 전략 수립 및 공시 준비",
        "category": "Framework",
    },
    
    # ===== 자연 자본 및 생태계 서비스 =====
    "Natural Capital": {
        "definition": "생태계 서비스를 제공하는 자연 자원 (물, 토양, 대기, 생물다양성 등)",
        "category": "Nature",
        "aliases": ["자연 자본", "자연자본"],
    },
    "Ecosystem Services": {
        "definition": "자연이 인간에게 제공하는 혜택 (공급, 조절, 문화, 지원 서비스)",
        "category": "Nature",
        "aliases": ["생태계 서비스"],
    },
    "Biodiversity": {
        "definition": "생물 다양성 - 종, 생태계, 유전자 수준의 다양성",
        "category": "Nature",
        "aliases": ["생물다양성", "생물 다양성"],
    },
    "Biome": {
        "definition": "특정 기후와 생태계 특성을 공유하는 대규모 생태 지역",
        "category": "Nature",
        "aliases": ["생물군계"],
    },
    
    # ===== 리스크 유형 =====
    "Physical Risk": {
        "definition": "자연 변화로 인한 직접적 물리적 영향 리스크 (급성/만성)",
        "category": "Risk",
        "aliases": ["물리적 리스크", "물리적 위험"],
    },
    "Acute Risk": {
        "definition": "급성 리스크 - 극단적 기상현상 등 단기 발생 위험",
        "category": "Risk",
        "aliases": ["급성 리스크"],
    },
    "Chronic Risk": {
        "definition": "만성 리스크 - 장기적으로 발생하는 점진적 변화 위험",
        "category": "Risk",
        "aliases": ["만성 리스크"],
    },
    "Transition Risk": {
        "definition": "이행 리스크 - 정책, 기술, 시장 변화로 인한 위험",
        "category": "Risk",
        "aliases": ["이행 리스크", "전환 리스크"],
    },
    "Water Stress": {
        "definition": "수자원 가용량 대비 수요 비율이 높은 상태",
        "category": "Risk",
        "aliases": ["물 스트레스", "수자원 부족"],
    },
    
    # ===== 변화 요인 =====
    "Driver of Change": {
        "definition": "자연 변화를 유발하는 요인 (토지이용 변화, 오염, 기후변화 등)",
        "category": "Impact",
        "aliases": ["변화 요인"],
    },
    "Land Use Change": {
        "definition": "토지 이용 변화 - 농업, 도시화 등으로 인한 서식지 변화",
        "category": "Impact",
        "aliases": ["토지이용 변화"],
    },
    "Pollution": {
        "definition": "대기, 수질, 토양 오염",
        "category": "Impact",
        "aliases": ["오염"],
    },
    "Overexploitation": {
        "definition": "자연 자원의 과도한 이용",
        "category": "Impact",
        "aliases": ["과잉 이용", "남용"],
    },
    
    # ===== 대응 조치 =====
    "Avoid": {
        "definition": "자연에 대한 영향/의존을 회피",
        "category": "Action",
        "aliases": ["회피"],
    },
    "Reduce": {
        "definition": "영향/의존을 최소화",
        "category": "Action",
        "aliases": ["저감", "감소"],
    },
    "Restore": {
        "definition": "손상된 생태계 복원",
        "category": "Action",
        "aliases": ["복원"],
    },
    "Regenerate": {
        "definition": "생태계 기능을 향상시키는 활동",
        "category": "Action",
        "aliases": ["재생"],
    },
    "Nature-based Solutions": {
        "definition": "자연 기반 해결책 - 생태계를 활용한 사회 문제 해결",
        "category": "Action",
        "aliases": ["자연기반해법", "NbS"],
    },
}


def find_terms_in_text(text: str) -> list[dict]:
    """
    텍스트에서 TNFD 용어를 식별합니다.
    
    Args:
        text: 검색할 텍스트
        
    Returns:
        발견된 용어 정보 리스트:
        - term: 용어
        - definition: 정의
        - category: 카테고리
        - position: 텍스트 내 위치
    """
    found_terms = []
    text_lower = text.lower()
    
    for term, info in TNFD_GLOSSARY.items():
        # 원래 용어 검색
        term_lower = term.lower()
        if term_lower in text_lower:
            pos = text_lower.find(term_lower)
            found_terms.append({
                "term": term,
                "definition": info["definition"],
                "category": info["category"],
                "position": pos,
            })
            continue
        
        # 별칭(aliases) 검색
        aliases = info.get("aliases", [])
        for alias in aliases:
            if alias.lower() in text_lower:
                pos = text_lower.find(alias.lower())
                found_terms.append({
                    "term": term,
                    "matched_alias": alias,
                    "definition": info["definition"],
                    "category": info["category"],
                    "position": pos,
                })
                break
    
    # 위치 순으로 정렬
    found_terms.sort(key=lambda x: x["position"])
    
    return found_terms


def get_terms_by_category(category: str) -> list[str]:
    """
    특정 카테고리의 용어 목록을 반환합니다.
    
    Args:
        category: 카테고리 (Framework, Nature, Risk, Impact, Action)
        
    Returns:
        해당 카테고리의 용어 리스트
    """
    return [
        term for term, info in TNFD_GLOSSARY.items()
        if info["category"] == category
    ]


def get_term_definition(term: str) -> Optional[str]:
    """
    용어의 정의를 반환합니다.
    
    Args:
        term: 검색할 용어
        
    Returns:
        용어 정의 (없으면 None)
    """
    if term in TNFD_GLOSSARY:
        return TNFD_GLOSSARY[term]["definition"]
    
    # 별칭으로 검색
    for t, info in TNFD_GLOSSARY.items():
        if term in info.get("aliases", []):
            return info["definition"]
    
    return None


if __name__ == "__main__":
    # 테스트
    sample_text = """
    Our company is assessing physical risks including water stress in our operations.
    We are implementing nature-based solutions to reduce our environmental impact.
    The LEAP framework helps us identify dependencies on ecosystem services.
    """
    
    print("=== TNFD 용어 식별 테스트 ===\n")
    print(f"입력 텍스트:\n{sample_text}\n")
    
    terms = find_terms_in_text(sample_text)
    print(f"발견된 용어 ({len(terms)}개):")
    for t in terms:
        print(f"  - {t['term']}: {t['definition'][:50]}...")
    
    print("\n=== 카테고리별 용어 ===")
    for cat in ["Framework", "Risk", "Action"]:
        terms = get_terms_by_category(cat)
        print(f"\n{cat}: {', '.join(terms[:5])}...")
