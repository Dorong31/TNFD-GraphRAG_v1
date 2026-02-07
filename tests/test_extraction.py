"""
Triple 추출 모듈 테스트

프롬프트 생성 및 결과 파싱 로직을 검증합니다.
(LLM API 호출은 모킹)
"""

import pytest
import json
from unittest.mock import Mock, patch

from src.extraction.prompts import build_extraction_prompt, SYSTEM_PROMPT
from src.schemas import RiskCategory, ActionType


class TestPromptBuilding:
    """프롬프트 생성 테스트"""
    
    def test_prompt_includes_text(self):
        """입력 텍스트가 프롬프트에 포함"""
        text = "Sample input text for testing"
        prompt = build_extraction_prompt(text)
        
        assert text in prompt
    
    def test_prompt_includes_system_prompt(self):
        """시스템 프롬프트가 포함"""
        prompt = build_extraction_prompt("test")
        
        assert "TNFD" in prompt
        assert "Organization" in prompt
    
    def test_prompt_includes_few_shot(self):
        """Few-shot 예시가 포함"""
        prompt = build_extraction_prompt("test", include_few_shot=True)
        
        # Few-shot 예시의 키워드 확인
        assert "Samsung Electronics" in prompt or "예시" in prompt
    
    def test_prompt_without_few_shot(self):
        """Few-shot 없이 생성 가능"""
        prompt = build_extraction_prompt("test", include_few_shot=False)
        
        # 프롬프트는 여전히 유효해야 함
        assert "test" in prompt


class TestExtractorParsing:
    """추출기 JSON 파싱 테스트"""
    
    def test_parse_valid_json_in_code_block(self):
        """코드 블록 내 JSON 파싱"""
        from src.extraction.extractor import TripleExtractor
        
        response = '''
```json
{
  "nodes": [{"name": "Test", "type": "Organization"}],
  "relationships": []
}
```
        '''
        
        # Mock LLM 없이 파싱 로직만 테스트
        extractor = Mock(spec=TripleExtractor)
        extractor._parse_json_response = TripleExtractor._parse_json_response.__get__(extractor)
        
        result = extractor._parse_json_response(response)
        
        assert result is not None
        assert len(result["nodes"]) == 1
    
    def test_parse_json_without_code_block(self):
        """코드 블록 없는 JSON 파싱"""
        from src.extraction.extractor import TripleExtractor
        
        response = '{"nodes": [], "relationships": []}'
        
        extractor = Mock(spec=TripleExtractor)
        extractor._parse_json_response = TripleExtractor._parse_json_response.__get__(extractor)
        
        result = extractor._parse_json_response(response)
        
        assert result is not None
        assert result["nodes"] == []


class TestNodeCreation:
    """노드 객체 생성 테스트"""
    
    def test_create_organization_from_dict(self):
        """딕셔너리에서 Organization 생성"""
        from src.extraction.extractor import TripleExtractor
        
        node_data = [{"name": "Test Corp", "type": "Organization"}]
        
        extractor = Mock(spec=TripleExtractor)
        extractor._create_nodes = TripleExtractor._create_nodes.__get__(extractor)
        
        nodes = extractor._create_nodes(node_data)
        
        assert len(nodes) == 1
        assert nodes[0].name == "Test Corp"
    
    def test_create_risk_with_category(self):
        """카테고리가 있는 Risk 생성"""
        from src.extraction.extractor import TripleExtractor
        
        node_data = [{"name": "Water Stress", "type": "Risk", "category": "Chronic"}]
        
        extractor = Mock(spec=TripleExtractor)
        extractor._create_nodes = TripleExtractor._create_nodes.__get__(extractor)
        
        nodes = extractor._create_nodes(node_data)
        
        assert len(nodes) == 1
        assert nodes[0].category == RiskCategory.CHRONIC
    
    def test_invalid_node_type_skipped(self):
        """잘못된 노드 타입은 건너뜀"""
        from src.extraction.extractor import TripleExtractor
        
        node_data = [
            {"name": "Valid", "type": "Organization"},
            {"name": "Invalid", "type": "UnknownType"},
        ]
        
        extractor = Mock(spec=TripleExtractor)
        extractor._create_nodes = TripleExtractor._create_nodes.__get__(extractor)
        
        nodes = extractor._create_nodes(node_data)
        
        # 유효한 노드만 생성됨
        assert len(nodes) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
