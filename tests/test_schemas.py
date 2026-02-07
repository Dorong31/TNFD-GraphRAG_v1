"""
스키마 테스트

노드 및 관계 스키마의 유효성을 검증합니다.
"""

import pytest
from src.schemas import (
    Organization, Location, Risk, Action, Evidence,
    Relationship, ExtractionResult,
    RiskCategory, ActionType, create_node
)


class TestNodeSchemas:
    """노드 스키마 테스트"""
    
    def test_organization_creation(self):
        """Organization 노드 생성 테스트"""
        org = Organization(name="Samsung Electronics", industry_code="C26")
        
        assert org.name == "Samsung Electronics"
        assert org.industry_code == "C26"
        assert org.node_type == "Organization"
        assert org.id == "org_samsung_electronics"
    
    def test_location_creation(self):
        """Location 노드 생성 테스트"""
        loc = Location(
            name="Vietnam Factory",
            country="Vietnam",
            biome_type="Tropical"
        )
        
        assert loc.name == "Vietnam Factory"
        assert loc.country == "Vietnam"
        assert loc.node_type == "Location"
        assert "vietnam_factory" in loc.id
    
    def test_risk_with_category(self):
        """Risk 노드 카테고리 테스트"""
        risk = Risk(
            name="Water Stress",
            category=RiskCategory.CHRONIC,
            description="지역 수자원 고갈"
        )
        
        assert risk.category == RiskCategory.CHRONIC
        assert risk.node_type == "Risk"
    
    def test_action_with_type(self):
        """Action 노드 타입 테스트"""
        action = Action(
            name="Water Recycling Program",
            action_type=ActionType.REDUCE,
            status="In Progress"
        )
        
        assert action.action_type == ActionType.REDUCE
        assert action.status == "In Progress"
    
    def test_evidence_id_generation(self):
        """Evidence 노드 ID 자동 생성 테스트"""
        ev = Evidence(
            text="Sample text content",
            source_doc="report_2024.pdf",
            page_num=10,
            chunk_index=5
        )
        
        assert "report_2024" in ev.id
        assert "p10" in ev.id
        assert "c5" in ev.id


class TestRelationshipSchema:
    """관계 스키마 테스트"""
    
    def test_relationship_creation(self):
        """관계 생성 테스트"""
        rel = Relationship(
            source_id="org_samsung",
            relationship_type="OPERATES_IN",
            target_id="loc_vietnam"
        )
        
        assert rel.source_id == "org_samsung"
        assert rel.relationship_type == "OPERATES_IN"
        assert rel.target_id == "loc_vietnam"
    
    def test_relationship_to_tuple(self):
        """관계 튜플 변환 테스트"""
        rel = Relationship(
            source_id="action_1",
            relationship_type="MITIGATES",
            target_id="risk_1"
        )
        
        expected = ("action_1", "MITIGATES", "risk_1")
        assert rel.to_tuple() == expected


class TestExtractionResult:
    """추출 결과 스키마 테스트"""
    
    def test_empty_result(self):
        """빈 추출 결과 테스트"""
        result = ExtractionResult()
        
        assert result.nodes == []
        assert result.relationships == []
        assert result.source_evidence_id is None
    
    def test_result_with_nodes(self):
        """노드가 있는 추출 결과 테스트"""
        org = Organization(name="Test Org")
        risk = Risk(name="Test Risk", category=RiskCategory.ACUTE)
        
        result = ExtractionResult(nodes=[org, risk])
        
        assert len(result.nodes) == 2


class TestNodeFactory:
    """노드 팩토리 함수 테스트"""
    
    def test_create_organization(self):
        """팩토리로 Organization 생성"""
        node = create_node("Organization", name="Test Corp")
        
        assert isinstance(node, Organization)
        assert node.name == "Test Corp"
    
    def test_create_risk(self):
        """팩토리로 Risk 생성"""
        node = create_node(
            "Risk",
            name="Flood",
            category=RiskCategory.ACUTE
        )
        
        assert isinstance(node, Risk)
        assert node.category == RiskCategory.ACUTE
    
    def test_invalid_node_type(self):
        """잘못된 노드 타입 예외 테스트"""
        with pytest.raises(ValueError) as exc_info:
            create_node("InvalidType", name="Test")
        
        assert "알 수 없는 노드 타입" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
