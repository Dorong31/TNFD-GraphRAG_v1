"""
하이브리드 검색 모듈

Vector 검색과 Keyword 검색을 결합하여 관련 노드를 찾고,
Graph Traversal을 통해 연결된 컨텍스트를 수집합니다.
"""

from typing import Optional

from src.config import GRAPH_TRAVERSAL_DEPTH, TOP_K_RESULTS
from src.graph.neo4j_client import Neo4jClient
from src.graph.vector_store import VectorStore


class HybridSearch:
    """
    하이브리드 검색 엔진
    
    1. Vector 검색: 질문과 의미적으로 유사한 Evidence 노드 검색
    2. Keyword 검색: 질문의 키워드와 일치하는 엔티티 노드 검색
    3. Graph Traversal: 검색된 노드로부터 연결된 이웃 노드 탐색
    """
    
    def __init__(
        self,
        neo4j_client: Optional[Neo4jClient] = None,
        vector_store: Optional[VectorStore] = None,
    ):
        """
        하이브리드 검색 초기화
        
        Args:
            neo4j_client: Neo4j 클라이언트 (없으면 새로 생성)
            vector_store: Vector Store (없으면 새로 생성)
        """
        self.neo4j = neo4j_client or Neo4jClient()
        self.vector_store = vector_store or VectorStore(neo4j_client=self.neo4j)
    
    def search(
        self,
        query: str,
        top_k: int = TOP_K_RESULTS,
        traversal_depth: int = GRAPH_TRAVERSAL_DEPTH,
        include_evidence: bool = True,
    ) -> dict:
        """
        하이브리드 검색을 수행합니다.
        
        Args:
            query: 검색 질의
            top_k: 반환할 최대 결과 수
            traversal_depth: 그래프 탐색 깊이
            include_evidence: Evidence 노드 포함 여부
            
        Returns:
            검색 결과 딕셔너리:
            - evidence: 유사한 Evidence 노드 리스트
            - entities: 관련 엔티티 노드 리스트
            - subgraph: 탐색된 서브그래프 (노드, 관계)
        """
        result = {
            "evidence": [],
            "entities": [],
            "subgraph": {"nodes": [], "relationships": []},
        }
        
        # 1. Vector 검색 - 유사한 Evidence 찾기
        if include_evidence:
            vector_results = self.vector_store.similarity_search(query, top_k=top_k)
            result["evidence"] = vector_results
        
        # 2. Keyword 검색 - 관련 엔티티 찾기
        keywords = self._extract_keywords(query)
        for keyword in keywords:
            entities = self.neo4j.search_nodes_by_name(keyword, limit=5)
            # 중복 제거
            for entity in entities:
                if entity not in result["entities"]:
                    result["entities"].append(entity)
        
        # 3. Graph Traversal - 앵커 노드로부터 이웃 탐색
        anchor_ids = self._get_anchor_node_ids(result)
        
        all_neighbors = []
        all_rels = []
        
        for node_id in anchor_ids[:5]:  # 상위 5개 앵커에서만 탐색 (성능 고려)
            neighbors = self.neo4j.get_neighbors(
                node_id, 
                depth=traversal_depth,
                direction="both"
            )
            all_neighbors.extend(neighbors.get("nodes", []))
            all_rels.extend(neighbors.get("relationships", []))
        
        # 중복 제거
        seen_ids = set()
        unique_nodes = []
        for node in all_neighbors:
            node_id = node.get("id", "")
            if node_id and node_id not in seen_ids:
                seen_ids.add(node_id)
                unique_nodes.append(node)
        
        result["subgraph"]["nodes"] = unique_nodes
        result["subgraph"]["relationships"] = all_rels
        
        return result
    
    def _extract_keywords(self, query: str) -> list[str]:
        """
        질의에서 검색 키워드를 추출합니다.
        
        간단한 규칙 기반 추출 (향후 NLP로 개선 가능)
        """
        # 불용어 목록 (한국어 + 영어)
        stopwords = {
            # 영어
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "need", "dare", "ought", "used", "to", "of", "in",
            "for", "on", "with", "at", "by", "from", "as", "into",
            "through", "during", "before", "after", "above", "below",
            "up", "down", "out", "off", "over", "under", "again",
            "further", "then", "once", "here", "there", "when", "where",
            "why", "how", "all", "each", "few", "more", "most", "other",
            "some", "such", "no", "nor", "not", "only", "own", "same",
            "so", "than", "too", "very", "just", "and", "but", "or",
            "what", "which", "who", "this", "that", "these", "those",
            # 한국어
            "의", "가", "이", "은", "를", "으로", "에", "와", "과", "도",
            "는", "에서", "한", "하는", "것", "등", "및", "또는", "있는",
            "없는", "된", "되는", "해", "하여", "위해", "대한", "통해",
            "무엇", "어떤", "어떻게", "왜", "있습니까", "입니까"
        }
        
        # 단어 분리 및 필터링
        words = query.lower().replace("?", "").replace(".", "").split()
        keywords = [
            word for word in words 
            if word not in stopwords and len(word) > 2
        ]
        
        return keywords
    
    def _get_anchor_node_ids(self, search_result: dict) -> list[str]:
        """
        검색 결과에서 그래프 탐색의 시작점(앵커) 노드 ID들을 추출합니다.
        """
        anchor_ids = []
        
        # Evidence 노드 ID 추가
        for ev in search_result.get("evidence", []):
            if ev_id := ev.get("id"):
                anchor_ids.append(ev_id)
        
        # 엔티티 노드 ID 추가
        for entity in search_result.get("entities", []):
            if ent_id := entity.get("id"):
                anchor_ids.append(ent_id)
        
        return anchor_ids
    
    def close(self):
        """리소스 정리"""
        self.vector_store.close()


def search(query: str, **kwargs) -> dict:
    """
    하이브리드 검색 편의 함수
    
    Args:
        query: 검색 질의
        **kwargs: HybridSearch.search()에 전달할 추가 인자
        
    Returns:
        검색 결과
    """
    searcher = HybridSearch()
    try:
        return searcher.search(query, **kwargs)
    finally:
        searcher.close()


if __name__ == "__main__":
    # 테스트
    print("=== 하이브리드 검색 테스트 ===\n")
    
    try:
        result = search("이 기업의 주요 물리적 리스크는 무엇입니까?", top_k=3)
        
        print(f"Evidence 검색 결과 ({len(result['evidence'])}개):")
        for ev in result['evidence'][:3]:
            print(f"  - [{ev.get('score', 0):.4f}] {ev.get('text', '')[:60]}...")
        
        print(f"\n엔티티 검색 결과 ({len(result['entities'])}개):")
        for ent in result['entities'][:5]:
            print(f"  - {ent.get('labels', [])}: {ent.get('name', ent.get('id', ''))}")
        
        print(f"\n서브그래프: {len(result['subgraph']['nodes'])} 노드")
        
    except Exception as e:
        print(f"오류: {e}")
