"""
Triple 추출 에이전트 모듈

LLM을 사용하여 텍스트에서 Knowledge Graph Triple(노드와 관계)을 추출합니다.
Google Gemini 모델을 기본으로 사용하며, 구조화된 출력을 생성합니다.
"""

import json
import re
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from src.config import GOOGLE_API_KEY, LLM_MODEL
from src.schemas import (
    Organization, Location, Risk, Action, Evidence,
    Relationship, ExtractionResult, RiskCategory, ActionType,
    create_node
)
from src.extraction.prompts import build_extraction_prompt


class TripleExtractor:
    """
    텍스트에서 Knowledge Graph Triple을 추출하는 에이전트
    
    LLM을 사용하여 텍스트를 분석하고 TNFD 온톨로지에 맞는
    노드(엔티티)와 관계를 추출합니다.
    """
    
    def __init__(self, model_name: str = LLM_MODEL, api_key: str = GOOGLE_API_KEY):
        """
        Triple 추출기 초기화
        
        Args:
            model_name: 사용할 LLM 모델명
            api_key: Google API 키
        """
        if not api_key:
            raise ValueError(
                "Google API 키가 설정되지 않았습니다. "
                ".env 파일에 GOOGLE_API_KEY를 설정하세요."
            )
        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.0,  # 일관된 추출을 위해 temperature 0
        )
    
    def extract(
        self, 
        text: str, 
        source_doc: str = "", 
        page_num: int = 0,
        chunk_index: int = 0
    ) -> ExtractionResult:
        """
        텍스트에서 Triple을 추출합니다.
        
        Args:
            text: 분석할 텍스트
            source_doc: 출처 문서명
            page_num: 페이지 번호
            chunk_index: 청크 인덱스
            
        Returns:
            ExtractionResult: 추출된 노드와 관계
        """
        # 텍스트가 너무 짧으면 추출하지 않음
        if len(text.strip()) < 50:
            return ExtractionResult()
        
        # 프롬프트 생성
        prompt = build_extraction_prompt(text)
        
        # LLM 호출
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_text = response.content
            # Google Gemini가 가끔 리스트 형태의 콘텐츠를 반환하는 경우 처리
            if isinstance(result_text, list):
                # 리스트 아이템이 포맷된 텍스트나 딕셔너리일 경우 처리
                text_parts = []
                for item in result_text:
                    if isinstance(item, str):
                        text_parts.append(item)
                    elif isinstance(item, dict) and 'text' in item:
                        text_parts.append(item['text'])
                    elif hasattr(item, 'text'):
                        text_parts.append(item.text)
                    else:
                        text_parts.append(str(item))
                result_text = "".join(text_parts)
        except Exception as e:
            print(f"LLM 호출 오류: {e}")
            return ExtractionResult()
        
        # JSON 파싱
        extracted_data = self._parse_json_response(result_text)
        if not extracted_data:
            return ExtractionResult()
        
        # Evidence 노드 생성 (출처 정보)
        evidence = Evidence(
            text=text,
            source_doc=source_doc,
            page_num=page_num,
            chunk_index=chunk_index
        )
        
        # 노드와 관계 객체로 변환
        nodes = self._create_nodes(extracted_data.get("nodes", []))
        relationships = self._create_relationships(
            extracted_data.get("relationships", []),
            evidence.id
        )
        
        # Evidence Linking: 모든 추출된 노드를 Evidence와 연결 (MENTIONS)
        # 원칙 1. 근거 기반 추출 (Evidence Grounding) 구현
        for node in nodes:
            relationships.append(Relationship(
                source_id=node.id,
                relationship_type="MENTIONS",
                target_id=evidence.id
            ))
        
        # Evidence 노드도 결과에 포함
        nodes.append(evidence)
        
        return ExtractionResult(
            nodes=nodes,
            relationships=relationships,
            source_evidence_id=evidence.id
        )
    
    def extract_batch(
        self, 
        chunks: list[dict],
        progress_callback: Optional[callable] = None
    ) -> list[ExtractionResult]:
        """
        여러 청크에서 Triple을 일괄 추출합니다.
        
        Args:
            chunks: 청크 딕셔너리 리스트 (text, source_doc, page_num, chunk_index)
            progress_callback: 진행률 콜백 함수 (현재 인덱스, 총 개수)
            
        Returns:
            ExtractionResult 리스트
        """
        results = []
        total = len(chunks)
        
        for i, chunk in enumerate(chunks):
            result = self.extract(
                text=chunk.get("text", ""),
                source_doc=chunk.get("source_doc", ""),
                page_num=chunk.get("page_num", 0),
                chunk_index=chunk.get("chunk_index", i)
            )
            results.append(result)
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return results
    
    def _parse_json_response(self, response_text: str) -> Optional[dict]:
        """
        LLM 응답에서 JSON을 파싱합니다.
        
        코드 블록(```json ... ```)이나 일반 JSON을 모두 처리합니다.
        """

        
        # 코드 블록에서 JSON 추출
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response_text)

        
        if json_match:
            json_str = json_match.group(1).strip()

        else:
            # 코드 블록 없이 JSON만 있는 경우
            json_str = response_text.strip()

        
        # JSON 파싱 시도
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # JSON 수정 시도 (흔한 오류 수정)
            try:
                # 후행 쉼표 제거
                fixed = re.sub(r',\s*}', '}', json_str)
                fixed = re.sub(r',\s*]', ']', fixed)
                return json.loads(fixed)
            except json.JSONDecodeError:
                print(f"JSON 파싱 실패: {e}")

                print(f"원본 텍스트: {json_str[:500]}...")
                return None
    
    def _create_nodes(self, node_data_list: list[dict]) -> list:
        """
        딕셔너리 리스트를 노드 객체 리스트로 변환합니다.
        """
        nodes = []
        
        for data in node_data_list:
            node_type = data.get("type", "")
            name = data.get("name", "")
            
            if not node_type or not name:
                continue
            
            try:
                if node_type == "Organization":
                    node = Organization(
                        name=name,
                        industry_code=data.get("industry_code")
                    )
                elif node_type == "Location":
                    node = Location(
                        name=name,
                        country=data.get("country"),
                        biome_type=data.get("biome_type")
                    )
                elif node_type == "Risk":
                    # 카테고리 매핑
                    category_str = data.get("category", "Chronic")
                    try:
                        category = RiskCategory(category_str)
                    except ValueError:
                        category = RiskCategory.CHRONIC
                    
                    node = Risk(
                        name=name,
                        category=category,
                        description=data.get("description"),
                        financial_impact=data.get("financial_impact")
                    )
                elif node_type == "Action":
                    # 액션 타입 매핑
                    action_type_str = data.get("action_type", "Reduce")
                    try:
                        action_type = ActionType(action_type_str)
                    except ValueError:
                        action_type = ActionType.REDUCE
                    
                    node = Action(
                        name=name,
                        action_type=action_type,
                        description=data.get("description"),
                        status=data.get("status")
                    )
                else:
                    continue
                
                nodes.append(node)
                
            except Exception as e:
                print(f"노드 생성 실패 ({name}): {e}")
                continue
        
        return nodes
    
    def _create_relationships(
        self, 
        rel_data_list: list[dict],
        evidence_id: str
    ) -> list[Relationship]:
        """
        딕셔너리 리스트를 관계 객체 리스트로 변환합니다.
        각 관계에 Evidence 연결도 추가합니다.
        """
        relationships = []
        
        for data in rel_data_list:
            source = data.get("source", "")
            relation = data.get("relation", "")
            target = data.get("target", "")
            
            if not all([source, relation, target]):
                continue
            
            # 소스/타겟 이름을 ID 형식으로 변환
            source_id = source.lower().replace(" ", "_")
            target_id = target.lower().replace(" ", "_")
            
            # 관계 생성
            rel = Relationship(
                source_id=source_id,
                relationship_type=relation,
                target_id=target_id
            )
            relationships.append(rel)
        
        return relationships


def extract_from_chunks(chunks: list[dict]) -> list[ExtractionResult]:
    """
    청크 리스트에서 Triple을 추출하는 편의 함수
    
    Args:
        chunks: chunker.create_chunks_from_pages()의 반환값
        
    Returns:
        ExtractionResult 리스트
    """
    extractor = TripleExtractor()
    return extractor.extract_batch(chunks)


if __name__ == "__main__":
    # 테스트
    print("=== Triple 추출 테스트 ===\n")
    
    test_text = """
    Samsung Electronics is implementing a comprehensive water management program 
    across its manufacturing facilities. The company faces significant water stress 
    risks in its Giheung campus in South Korea. To mitigate these risks, Samsung 
    has installed advanced water recycling systems that reduce freshwater consumption 
    by 30%.
    """
    
    try:
        extractor = TripleExtractor()
        result = extractor.extract(
            text=test_text,
            source_doc="test_report.pdf",
            page_num=1,
            chunk_index=0
        )
        
        print(f"추출된 노드 ({len(result.nodes)}개):")
        for node in result.nodes:
            print(f"  - [{node.node_type}] {node.name if hasattr(node, 'name') else node.id}")
        
        print(f"\n추출된 관계 ({len(result.relationships)}개):")
        for rel in result.relationships:
            print(f"  - {rel.to_tuple()}")
            
    except ValueError as e:
        print(f"오류: {e}")
        print("테스트를 실행하려면 .env 파일에 GOOGLE_API_KEY를 설정하세요.")
