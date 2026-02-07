"""
Neo4j 클라이언트 모듈

Neo4j 그래프 데이터베이스와의 연결 및 CRUD 작업을 수행합니다.
노드 생성, 관계 생성, 쿼리 실행 등의 기능을 제공합니다.
"""

from typing import Optional, Any
from contextlib import contextmanager

from neo4j import GraphDatabase, Driver

from src.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, RELATIONSHIP_TYPES
from src.schemas import (
    Organization, Location, Risk, Action, Evidence,
    Relationship, ExtractionResult
)


class Neo4jClient:
    """
    Neo4j 그래프 데이터베이스 클라이언트
    
    Knowledge Graph의 노드와 관계를 Neo4j에 저장하고 조회합니다.
    """
    
    def __init__(
        self,
        uri: str = NEO4J_URI,
        username: str = NEO4J_USERNAME,
        password: str = NEO4J_PASSWORD,
    ):
        """
        Neo4j 클라이언트 초기화
        
        Args:
            uri: Neo4j 연결 URI (예: neo4j://localhost:7687)
            username: Neo4j 사용자명
            password: Neo4j 비밀번호
        """
        if not password:
            raise ValueError(
                "Neo4j 비밀번호가 설정되지 않았습니다. "
                ".env 파일에 NEO4J_PASSWORD를 설정하세요."
            )
        
        self.driver: Driver = GraphDatabase.driver(uri, auth=(username, password))
        self._verify_connection()
    
    def _verify_connection(self):
        """연결 상태를 확인합니다."""
        try:
            self.driver.verify_connectivity()
        except Exception as e:
            raise ConnectionError(f"Neo4j 연결 실패: {e}")
    
    def close(self):
        """드라이버 연결을 종료합니다."""
        self.driver.close()
    
    @contextmanager
    def session(self):
        """세션 컨텍스트 매니저"""
        session = self.driver.session()
        try:
            yield session
        finally:
            session.close()
    
    # ============ 노드 CRUD ============
    
    def create_node(self, node: Any) -> str:
        """
        노드를 생성하거나 기존 노드를 업데이트합니다 (MERGE).
        
        Args:
            node: 스키마 노드 객체 (Organization, Location, Risk, Action, Evidence)
            
        Returns:
            생성/갱신된 노드의 ID
        """
        node_type = node.node_type
        properties = node.model_dump(exclude={"node_type", "embedding"})
        
        # Cypher 쿼리: MERGE로 중복 방지
        query = f"""
        MERGE (n:{node_type} {{id: $id}})
        SET n += $properties
        RETURN n.id as id
        """
        
        with self.session() as session:
            result = session.run(query, id=node.id, properties=properties)
            record = result.single()
            return record["id"] if record else node.id
    
    def create_nodes_batch(self, nodes: list) -> int:
        """
        여러 노드를 일괄 생성합니다.
        
        Args:
            nodes: 노드 객체 리스트
            
        Returns:
            생성된 노드 수
        """
        created = 0
        for node in nodes:
            try:
                self.create_node(node)
                created += 1
            except Exception as e:
                print(f"노드 생성 실패 ({node.id}): {e}")
        return created
    
    def get_node_by_id(self, node_id: str) -> Optional[dict]:
        """
        ID로 노드를 조회합니다.
        
        Args:
            node_id: 노드 ID
            
        Returns:
            노드 속성 딕셔너리 (없으면 None)
        """
        query = """
        MATCH (n {id: $id})
        RETURN n, labels(n) as labels
        """
        
        with self.session() as session:
            result = session.run(query, id=node_id)
            record = result.single()
            if record:
                node_data = dict(record["n"])
                node_data["labels"] = record["labels"]
                return node_data
            return None
    
    def search_nodes_by_name(
        self, 
        name_query: str, 
        node_type: Optional[str] = None,
        limit: int = 10
    ) -> list[dict]:
        """
        이름으로 노드를 검색합니다 (부분 일치).
        
        Args:
            name_query: 검색할 이름
            node_type: 특정 노드 타입으로 제한 (선택)
            limit: 최대 결과 수
            
        Returns:
            노드 딕셔너리 리스트
        """
        if node_type:
            query = f"""
            MATCH (n:{node_type})
            WHERE n.name CONTAINS $name_query
            RETURN n, labels(n) as labels
            LIMIT $limit
            """
        else:
            query = """
            MATCH (n)
            WHERE n.name CONTAINS $name_query
            RETURN n, labels(n) as labels
            LIMIT $limit
            """
        
        with self.session() as session:
            result = session.run(query, name_query=name_query, limit=limit)
            nodes = []
            for record in result:
                node_data = dict(record["n"])
                node_data["labels"] = record["labels"]
                nodes.append(node_data)
            return nodes
    
    # ============ 관계 CRUD ============
    
    def create_relationship(self, relationship: Relationship) -> bool:
        """
        노드 간 관계를 생성합니다.
        
        Args:
            relationship: 관계 객체
            
        Returns:
            성공 여부
        """
        rel_type = relationship.relationship_type
        properties = relationship.properties or {}
        
        # 관계 타입 검증
        if rel_type not in RELATIONSHIP_TYPES:
            print(f"경고: 정의되지 않은 관계 타입: {rel_type}")
        
        # Cypher 쿼리: 양쪽 노드가 존재해야 관계 생성
        query = f"""
        MATCH (source {{id: $source_id}})
        MATCH (target {{id: $target_id}})
        MERGE (source)-[r:{rel_type}]->(target)
        SET r += $properties
        RETURN type(r) as rel_type
        """
        
        with self.session() as session:
            try:
                result = session.run(
                    query,
                    source_id=relationship.source_id,
                    target_id=relationship.target_id,
                    properties=properties
                )
                record = result.single()
                return record is not None
            except Exception as e:
                print(f"관계 생성 실패: {e}")
                return False
    
    def create_relationships_batch(self, relationships: list[Relationship]) -> int:
        """
        여러 관계를 일괄 생성합니다.
        
        Args:
            relationships: 관계 객체 리스트
            
        Returns:
            생성된 관계 수
        """
        created = 0
        for rel in relationships:
            if self.create_relationship(rel):
                created += 1
        return created
    
    # ============ 그래프 탐색 ============
    
    def get_neighbors(
        self, 
        node_id: str, 
        depth: int = 1,
        direction: str = "both"
    ) -> dict:
        """
        노드의 이웃 노드들을 탐색합니다.
        
        Args:
            node_id: 시작 노드 ID
            depth: 탐색 깊이 (hop 수)
            direction: 탐색 방향 ("in", "out", "both")
            
        Returns:
            탐색 결과 (nodes, relationships)
        """
        # 방향에 따른 관계 패턴
        if direction == "in":
            rel_pattern = "<-[r*1.." + str(depth) + "]-"
        elif direction == "out":
            rel_pattern = "-[r*1.." + str(depth) + "]->"
        else:  # both
            rel_pattern = "-[r*1.." + str(depth) + "]-"
        
        query = f"""
        MATCH (start {{id: $node_id}})
        OPTIONAL MATCH path = (start){rel_pattern}(neighbor)
        WITH start, neighbor, relationships(path) as rels
        WHERE neighbor IS NOT NULL
        RETURN 
            collect(DISTINCT neighbor) as neighbors,
            collect(DISTINCT rels) as relationships
        """
        
        with self.session() as session:
            result = session.run(query, node_id=node_id)
            record = result.single()
            
            if not record:
                return {"nodes": [], "relationships": []}
            
            return {
                "nodes": [dict(n) for n in record["neighbors"]],
                "relationships": record["relationships"]
            }
    
    # ============ 유틸리티 ============
    
    def clear_database(self):
        """
        데이터베이스의 모든 노드와 관계를 삭제합니다.
        
        주의: 이 작업은 되돌릴 수 없습니다!
        """
        query = "MATCH (n) DETACH DELETE n"
        with self.session() as session:
            session.run(query)
    
    def get_statistics(self) -> dict:
        """
        데이터베이스 통계를 반환합니다.
        
        Returns:
            노드 수, 관계 수, 노드 타입별 카운트
        """
        query = """
        MATCH (n)
        WITH labels(n) as label, count(n) as count
        RETURN label[0] as node_type, count
        ORDER BY count DESC
        """
        
        with self.session() as session:
            result = session.run(query)
            type_counts = {record["node_type"]: record["count"] for record in result}
        
        # 전체 통계
        total_query = """
        MATCH (n)
        OPTIONAL MATCH ()-[r]->()
        RETURN count(DISTINCT n) as node_count, count(DISTINCT r) as rel_count
        """
        
        with self.session() as session:
            result = session.run(total_query)
            record = result.single()
        
        return {
            "total_nodes": record["node_count"] if record else 0,
            "total_relationships": record["rel_count"] if record else 0,
            "nodes_by_type": type_counts
        }
    
    def save_extraction_result(self, result: ExtractionResult) -> dict:
        """
        추출 결과를 그래프에 저장합니다.
        
        Args:
            result: ExtractionResult 객체
            
        Returns:
            저장 통계 (created_nodes, created_relationships)
        """
        nodes_created = self.create_nodes_batch(result.nodes)
        rels_created = self.create_relationships_batch(result.relationships)
        
        return {
            "nodes_created": nodes_created,
            "relationships_created": rels_created
        }


if __name__ == "__main__":
    # 테스트
    print("=== Neo4j 클라이언트 테스트 ===\n")
    
    try:
        client = Neo4jClient()
        print("✓ Neo4j 연결 성공")
        
        # 통계 조회
        stats = client.get_statistics()
        print(f"\n현재 그래프 통계:")
        print(f"  - 총 노드 수: {stats['total_nodes']}")
        print(f"  - 총 관계 수: {stats['total_relationships']}")
        
        if stats['nodes_by_type']:
            print("  - 노드 타입별:")
            for t, c in stats['nodes_by_type'].items():
                print(f"      {t}: {c}")
        
        client.close()
        
    except ValueError as e:
        print(f"설정 오류: {e}")
    except ConnectionError as e:
        print(f"연결 오류: {e}")
