"""
답변 생성 모듈

검색 결과를 바탕으로 LLM을 사용하여 사용자 질문에 답변을 생성합니다.
출처(Citation)와 근거를 함께 제시합니다.
"""

from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import GOOGLE_API_KEY, LLM_MODEL
from src.retrieval.hybrid_search import HybridSearch


# ============ 시스템 프롬프트 ============
GENERATOR_SYSTEM_PROMPT = """당신은 TNFD(자연 관련 재무 정보 공개) 전문 분석가입니다.
제공된 컨텍스트를 바탕으로 사용자의 질문에 정확하게 답변하세요.

## 규칙
1. **컨텍스트 기반 답변**: 제공된 Evidence와 그래프 정보만을 사용하여 답변하세요.
2. **출처 표기**: 답변에 사용한 정보의 출처를 [문서명, 페이지] 형식으로 표기하세요.
3. **TNFD 용어 사용**: 가능한 TNFD 프레임워크의 전문 용어를 사용하세요.
4. **구조화된 답변**: 리스크, 조치, 위치 등 유형별로 구분하여 명확하게 답변하세요.
5. **불확실성 표시**: 정보가 불충분하면 솔직히 "제공된 정보로는 확인할 수 없습니다"라고 답변하세요.
6. **한국어 답변**: 질문이 한국어이면 한국어로, 영어이면 영어로 답변하세요.
"""


class AnswerGenerator:
    """
    RAG 기반 답변 생성기
    
    하이브리드 검색 결과를 컨텍스트로 사용하여
    LLM이 질문에 대한 답변을 생성합니다.
    """
    
    def __init__(
        self,
        model_name: str = LLM_MODEL,
        api_key: str = GOOGLE_API_KEY,
        searcher: Optional[HybridSearch] = None,
    ):
        """
        답변 생성기 초기화
        
        Args:
            model_name: LLM 모델명
            api_key: Google API 키
            searcher: 하이브리드 검색 엔진 (없으면 새로 생성)
        """
        if not api_key:
            raise ValueError("Google API 키가 설정되지 않았습니다.")
        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.3,  # 약간의 창의성 허용
        )
        self.searcher = searcher or HybridSearch()
    
    def generate(
        self,
        question: str,
        top_k: int = 5,
        include_sources: bool = True,
    ) -> dict:
        """
        질문에 대한 답변을 생성합니다.
        
        Args:
            question: 사용자 질문
            top_k: 검색할 Evidence 수
            include_sources: 출처 정보 포함 여부
            
        Returns:
            답변 결과 딕셔너리:
            - answer: 생성된 답변
            - sources: 출처 정보 리스트
            - context_used: 사용된 컨텍스트 요약
        """
        # 1. 하이브리드 검색 수행
        search_results = self.searcher.search(question, top_k=top_k)
        
        # 2. 컨텍스트 조합
        context = self._build_context(search_results)
        
        if not context.strip():
            return {
                "answer": "관련 정보를 찾을 수 없습니다. 다른 질문을 해주세요.",
                "sources": [],
                "context_used": ""
            }
        
        # 3. 프롬프트 생성
        prompt = self._build_prompt(question, context)
        
        # 4. LLM 호출
        try:
            response = self.llm.invoke([
                SystemMessage(content=GENERATOR_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ])
            answer = response.content
        except Exception as e:
            print(f"LLM 호출 오류: {e}")
            answer = "답변 생성 중 오류가 발생했습니다."
        
        # 5. 출처 정보 추출
        sources = []
        if include_sources:
            sources = self._extract_sources(search_results)
        
        return {
            "answer": answer,
            "sources": sources,
            "context_used": context[:500] + "..." if len(context) > 500 else context
        }
    
    def _build_context(self, search_results: dict) -> str:
        """
        검색 결과로부터 LLM 컨텍스트를 구성합니다.
        """
        context_parts = []
        
        # Evidence 추가
        evidence_list = search_results.get("evidence", [])
        if evidence_list:
            context_parts.append("## 관련 문서 내용 (Evidence)")
            for i, ev in enumerate(evidence_list, 1):
                text = ev.get("text", "")
                source = ev.get("source_doc", "Unknown")
                page = ev.get("page_num", "?")
                context_parts.append(
                    f"\n### Evidence {i} [{source}, p.{page}]\n{text}"
                )
        
        # 엔티티 정보 추가
        entities = search_results.get("entities", [])
        if entities:
            context_parts.append("\n## 관련 엔티티")
            for ent in entities:
                labels = ent.get("labels", [])
                name = ent.get("name", ent.get("id", "Unknown"))
                label_str = ", ".join(labels) if labels else "Unknown"
                
                # 추가 속성
                props = []
                for key in ["category", "action_type", "country", "description"]:
                    if val := ent.get(key):
                        props.append(f"{key}: {val}")
                
                prop_str = f" ({', '.join(props)})" if props else ""
                context_parts.append(f"- **{name}** [{label_str}]{prop_str}")
        
        # 서브그래프 관계 추가
        subgraph = search_results.get("subgraph", {})
        nodes = subgraph.get("nodes", [])
        if nodes:
            context_parts.append(f"\n## 연결된 컨텍스트 ({len(nodes)}개 노드)")
            for node in nodes[:10]:  # 최대 10개
                name = node.get("name", node.get("id", "Unknown"))
                node_type = node.get("labels", ["Unknown"])[0] if "labels" in node else "Unknown"
                context_parts.append(f"- {node_type}: {name}")
        
        return "\n".join(context_parts)
    
    def _build_prompt(self, question: str, context: str) -> str:
        """
        답변 생성 프롬프트를 구성합니다.
        """
        return f"""
## 컨텍스트
{context}

---

## 질문
{question}

---

위 컨텍스트를 바탕으로 질문에 답변하세요. 
답변에 사용한 정보의 출처를 [문서명, 페이지] 형식으로 표기하세요.
"""
    
    def _extract_sources(self, search_results: dict) -> list[dict]:
        """
        검색 결과에서 출처 정보를 추출합니다.
        """
        sources = []
        for ev in search_results.get("evidence", []):
            sources.append({
                "document": ev.get("source_doc", "Unknown"),
                "page": ev.get("page_num", 0),
                "relevance_score": ev.get("score", 0),
                "preview": ev.get("text", "")[:100] + "...",
            })
        return sources
    
    def close(self):
        """리소스 정리"""
        self.searcher.close()


def query(question: str, **kwargs) -> str:
    """
    질의응답 편의 함수
    
    Args:
        question: 사용자 질문
        **kwargs: AnswerGenerator.generate()에 전달할 추가 인자
        
    Returns:
        생성된 답변 문자열
    """
    generator = AnswerGenerator()
    try:
        result = generator.generate(question, **kwargs)
        return result["answer"]
    finally:
        generator.close()


def query_with_sources(question: str, **kwargs) -> dict:
    """
    출처 정보를 포함한 질의응답
    
    Args:
        question: 사용자 질문
        **kwargs: 추가 인자
        
    Returns:
        답변과 출처를 포함한 딕셔너리
    """
    generator = AnswerGenerator()
    try:
        return generator.generate(question, **kwargs)
    finally:
        generator.close()


if __name__ == "__main__":
    # 테스트
    print("=== 답변 생성 테스트 ===\n")
    
    test_question = "이 기업의 주요 물리적 리스크는 무엇입니까?"
    print(f"질문: {test_question}\n")
    
    try:
        result = query_with_sources(test_question)
        
        print("답변:")
        print(result["answer"])
        
        print("\n출처:")
        for src in result["sources"]:
            print(f"  - {src['document']}, p.{src['page']} (score: {src['relevance_score']:.4f})")
        
    except Exception as e:
        print(f"오류: {e}")
        print("테스트를 실행하려면 Neo4j와 API 키가 설정되어 있어야 합니다.")
