"""
TNFD-GraphRAG 온톨로지 스키마 정의

이 모듈은 Knowledge Graph에서 사용하는 노드(엔티티)와 관계의 
Pydantic 모델을 정의합니다.

Phase 1 MVP에서는 5개의 핵심 노드 타입을 구현합니다:
- Organization: 분석 대상 기업/조직
- Location: 사업장 또는 자산의 위치  
- Risk: 물리적/이행 리스크
- Action: 완화 조치 및 전략
- Evidence: 정보 출처 (텍스트 청크)
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


# ============ 열거형 정의 ============

class RiskCategory(str, Enum):
    """
    리스크 분류 (TNFD 프레임워크 기준)
    
    - ACUTE: 급성 물리적 리스크 (예: 홍수, 태풍)
    - CHRONIC: 만성 물리적 리스크 (예: 수자원 고갈, 토양 침식)
    - TRANSITION: 이행 리스크 (예: 정책 변화, 기술 변화)
    """
    ACUTE = "Acute"
    CHRONIC = "Chronic"
    TRANSITION = "Transition"


class ActionType(str, Enum):
    """
    완화 조치 유형 (TNFD 권장 분류)
    
    - AVOID: 회피 (자연에 대한 영향/의존 회피)
    - REDUCE: 감소 (영향/의존 최소화)
    - RESTORE: 복원 (손상된 생태계 복원)
    - REGENERATE: 재생 (생태계 기능 향상)
    """
    AVOID = "Avoid"
    REDUCE = "Reduce"
    RESTORE = "Restore"
    REGENERATE = "Regenerate"


class NodeType(str, Enum):
    """그래프에서 사용하는 노드 타입"""
    ORGANIZATION = "Organization"
    LOCATION = "Location"
    RISK = "Risk"
    ACTION = "Action"
    EVIDENCE = "Evidence"


# ============ 노드 스키마 정의 ============

class BaseNode(BaseModel):
    """
    모든 노드의 기본 클래스
    
    공통 속성:
    - id: 노드 고유 식별자 (자동 생성 또는 이름 기반)
    - node_type: 노드 타입 (자동 설정)
    """
    id: Optional[str] = Field(default=None, description="노드 고유 식별자")
    
    class Config:
        # Pydantic V2 설정
        use_enum_values = True  # Enum 값을 문자열로 직렬화


class Organization(BaseNode):
    """
    분석 대상 기업/조직을 나타내는 노드
    
    예시: "Samsung Electronics", "SK Hynix"
    """
    name: str = Field(..., description="기업/조직명")
    industry_code: Optional[str] = Field(
        default=None, 
        description="ISIC 산업 분류 코드 (예: 'C26' = 전자제품 제조)"
    )
    node_type: Literal["Organization"] = "Organization"
    
    def __init__(self, **data):
        super().__init__(**data)
        # ID가 없으면 name을 기반으로 생성
        if not self.id:
            self.id = f"org_{self.name.lower().replace(' ', '_')}"


class Location(BaseNode):
    """
    사업장 또는 자산의 위치를 나타내는 노드
    
    예시: "Vietnam Factory", "Seoul Headquarters"
    """
    name: str = Field(..., description="위치명")
    coordinates: Optional[tuple[float, float]] = Field(
        default=None, 
        description="좌표 (위도, 경도)"
    )
    country: Optional[str] = Field(default=None, description="국가명")
    biome_type: Optional[str] = Field(
        default=None, 
        description="생태계 유형 (예: Tropical Forest, River)"
    )
    node_type: Literal["Location"] = "Location"
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            self.id = f"loc_{self.name.lower().replace(' ', '_')}"


class Risk(BaseNode):
    """
    물리적/이행 리스크를 나타내는 노드
    
    예시: "Water Stress", "Extreme Heat", "Regulatory Changes"
    """
    name: str = Field(..., description="리스크명")
    category: RiskCategory = Field(..., description="리스크 분류")
    description: Optional[str] = Field(default=None, description="리스크 상세 설명")
    financial_impact: Optional[str] = Field(
        default=None, 
        description="예상 재무 영향 (정성적 설명)"
    )
    node_type: Literal["Risk"] = "Risk"
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            self.id = f"risk_{self.name.lower().replace(' ', '_')}"


class Action(BaseNode):
    """
    완화 조치 및 전략을 나타내는 노드
    
    예시: "Regenerative Agriculture", "Water Recycling Program"
    """
    name: str = Field(..., description="조치/전략명")
    action_type: ActionType = Field(..., description="조치 유형")
    description: Optional[str] = Field(default=None, description="조치 상세 설명")
    status: Optional[str] = Field(
        default=None, 
        description="이행 상태 (예: Planned, In Progress, Completed)"
    )
    node_type: Literal["Action"] = "Action"
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            self.id = f"action_{self.name.lower().replace(' ', '_')}"


class Evidence(BaseNode):
    """
    정보의 출처를 나타내는 노드 (텍스트 청크)
    
    각 Evidence 노드는 원본 문서의 특정 부분을 참조하며,
    다른 노드들의 근거 자료로 연결됩니다.
    """
    text: str = Field(..., description="원문 텍스트 내용")
    source_doc: str = Field(..., description="출처 문서 파일명")
    page_num: int = Field(..., description="페이지 번호")
    chunk_index: Optional[int] = Field(default=None, description="청크 인덱스")
    embedding: Optional[list[float]] = Field(
        default=None, 
        description="텍스트 임베딩 벡터",
        exclude=True  # JSON 직렬화 시 제외 (용량 절약)
    )
    node_type: Literal["Evidence"] = "Evidence"
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            # 문서명과 페이지, 청크 인덱스로 고유 ID 생성
            doc_name = self.source_doc.replace('.pdf', '').replace(' ', '_')
            chunk_id = self.chunk_index if self.chunk_index is not None else 0
            self.id = f"ev_{doc_name}_p{self.page_num}_c{chunk_id}"


# ============ 관계 스키마 정의 ============

class Relationship(BaseModel):
    """
    두 노드 간의 관계를 나타내는 모델
    
    예시: ("Samsung", "OPERATES_IN", "Vietnam Factory")
    """
    source_id: str = Field(..., description="출발 노드 ID")
    relationship_type: str = Field(..., description="관계 유형")
    target_id: str = Field(..., description="도착 노드 ID")
    properties: Optional[dict] = Field(
        default=None, 
        description="관계에 부가되는 속성 (예: since_year)"
    )
    
    def to_tuple(self) -> tuple[str, str, str]:
        """관계를 (source, type, target) 튜플로 반환"""
        return (self.source_id, self.relationship_type, self.target_id)


# ============ 추출 결과 스키마 ============

class ExtractionResult(BaseModel):
    """
    LLM Triple 추출 결과를 담는 모델
    
    하나의 텍스트 청크에서 추출된 노드와 관계의 집합
    """
    nodes: list[Organization | Location | Risk | Action | Evidence] = Field(
        default_factory=list,
        description="추출된 노드 리스트"
    )
    relationships: list[Relationship] = Field(
        default_factory=list,
        description="추출된 관계 리스트"
    )
    source_evidence_id: Optional[str] = Field(
        default=None,
        description="이 추출 결과의 근거가 되는 Evidence 노드 ID"
    )


# ============ 편의 함수 ============

def create_node(node_type: str, **kwargs) -> BaseNode:
    """
    노드 타입 문자열을 기반으로 적절한 노드 객체를 생성합니다.
    
    Args:
        node_type: 노드 타입 문자열 (Organization, Location, Risk, Action, Evidence)
        **kwargs: 노드 속성
        
    Returns:
        해당 타입의 노드 객체
        
    Raises:
        ValueError: 알 수 없는 노드 타입인 경우
    """
    node_classes = {
        "Organization": Organization,
        "Location": Location,
        "Risk": Risk,
        "Action": Action,
        "Evidence": Evidence,
    }
    
    if node_type not in node_classes:
        raise ValueError(f"알 수 없는 노드 타입: {node_type}. 가능한 타입: {list(node_classes.keys())}")
    
    return node_classes[node_type](**kwargs)


if __name__ == "__main__":
    # 스키마 테스트
    print("=== TNFD-GraphRAG 스키마 테스트 ===\n")
    
    # 노드 생성 테스트
    org = Organization(name="Samsung Electronics", industry_code="C26")
    print(f"Organization: {org.model_dump()}\n")
    
    loc = Location(name="Vietnam Factory", country="Vietnam", biome_type="Tropical")
    print(f"Location: {loc.model_dump()}\n")
    
    risk = Risk(
        name="Water Stress", 
        category=RiskCategory.CHRONIC,
        description="지역 수자원 고갈로 인한 제조 공정 영향"
    )
    print(f"Risk: {risk.model_dump()}\n")
    
    action = Action(
        name="Water Recycling Program",
        action_type=ActionType.REDUCE,
        status="In Progress"
    )
    print(f"Action: {action.model_dump()}\n")
    
    evidence = Evidence(
        text="당사는 베트남 공장에서 물 재활용 프로그램을 시행 중입니다.",
        source_doc="sustainability_report_2024.pdf",
        page_num=45
    )
    print(f"Evidence: {evidence.model_dump()}\n")
    
    # 관계 생성 테스트
    rel = Relationship(
        source_id=org.id,
        relationship_type="OPERATES_IN",
        target_id=loc.id
    )
    print(f"Relationship: {rel.to_tuple()}")
