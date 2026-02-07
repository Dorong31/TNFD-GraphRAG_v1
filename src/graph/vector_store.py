"""
Vector Store 모듈

Neo4j의 Vector Index를 사용하여 Evidence 노드의 텍스트 임베딩을 저장하고
유사도 검색을 수행합니다.

Google Gemini Embedding 모델(gemini-embedding-001)을 사용하여
768차원의 임베딩 벡터를 생성합니다.
"""

from typing import Optional
from google import genai
from google.genai import types

from src.config import (
    GOOGLE_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIMENSION, TOP_K_RESULTS
)
from src.graph.neo4j_client import Neo4jClient


class GeminiEmbeddings:
    """
    Google Gemini 임베딩 모델 래퍼 클래스
    
    gemini-embedding-001 모델을 사용하여 768차원 임베딩을 생성합니다.
    LangChain 호환 인터페이스를 제공합니다.
    """
    
    def __init__(self, model_name: str = EMBEDDING_MODEL, api_key: str = GOOGLE_API_KEY):
        """
        Gemini 임베딩 초기화
        
        Args:
            model_name: 임베딩 모델명 (기본: models/gemini-embedding-001)
            api_key: Google API 키
        """
        if not api_key:
            raise ValueError(
                "Google API 키가 설정되지 않았습니다. "
                ".env 파일에 GOOGLE_API_KEY를 설정하세요."
            )
        
        # 새로운 google-genai 클라이언트 초기화
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
    
    def embed_query(self, text: str) -> list[float]:
        """
        단일 텍스트를 임베딩합니다 (검색 쿼리용).
        
        Args:
            text: 임베딩할 텍스트
            
        Returns:
            768차원 임베딩 벡터
        """
        result = self.client.models.embed_content(
            model=self.model_name,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",  # 검색 쿼리용
                output_dimensionality=EMBEDDING_DIMENSION,  # 768차원
            )
        )
        return result.embeddings[0].values
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        여러 텍스트를 임베딩합니다 (문서용).
        
        Args:
            texts: 임베딩할 텍스트 리스트
            
        Returns:
            768차원 임베딩 벡터 리스트
        """
        embeddings = []
        for text in texts:
            result = self.client.models.embed_content(
                model=self.model_name,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",  # 문서 저장용
                    output_dimensionality=EMBEDDING_DIMENSION,
                )
            )
            embeddings.append(result.embeddings[0].values)
        return embeddings


class VectorStore:
    """
    Neo4j 기반 Vector Store
    
    Evidence 노드의 텍스트를 임베딩하여 저장하고
    의미 기반 유사도 검색을 수행합니다.
    
    Google Gemini Embedding(768차원)을 사용합니다.
    """
    
    INDEX_NAME = "evidence_embedding"  # Neo4j Vector Index 이름
    
    def __init__(
        self,
        neo4j_client: Optional[Neo4jClient] = None,
        embedding_model: str = EMBEDDING_MODEL,
    ):
        """
        Vector Store 초기화
        
        Args:
            neo4j_client: Neo4j 클라이언트 (없으면 새로 생성)
            embedding_model: 임베딩 모델명
        """
        self.client = neo4j_client or Neo4jClient()
        
        # Google Gemini 임베딩 모델 사용
        self.embeddings = GeminiEmbeddings(model_name=embedding_model)
    
    def create_vector_index(self):
        """
        Neo4j에 Vector Index를 생성합니다.
        
        이미 존재하면 건너뜁니다.
        768차원 벡터를 위한 인덱스를 생성합니다.
        """
        query = f"""
        CREATE VECTOR INDEX {self.INDEX_NAME} IF NOT EXISTS
        FOR (e:Evidence)
        ON e.embedding
        OPTIONS {{
            indexConfig: {{
                `vector.dimensions`: {EMBEDDING_DIMENSION},
                `vector.similarity_function`: 'cosine'
            }}
        }}
        """
        
        with self.client.session() as session:
            try:
                session.run(query)
                print(f"✓ Vector Index '{self.INDEX_NAME}' 생성/확인 완료 ({EMBEDDING_DIMENSION}차원)")
            except Exception as e:
                print(f"Vector Index 생성 경고: {e}")
    
    def embed_and_store(
        self, 
        text: str, 
        evidence_id: str
    ) -> bool:
        """
        텍스트를 임베딩하여 Evidence 노드에 저장합니다.
        
        Args:
            text: 임베딩할 텍스트
            evidence_id: 대상 Evidence 노드 ID
            
        Returns:
            성공 여부
        """
        # 임베딩 생성
        try:
            embedding = self.embeddings.embed_query(text)
        except Exception as e:
            print(f"임베딩 생성 실패: {e}")
            return False
        
        # Neo4j에 저장
        query = """
        MATCH (e:Evidence {id: $id})
        SET e.embedding = $embedding
        RETURN e.id as id
        """
        
        with self.client.session() as session:
            try:
                result = session.run(query, id=evidence_id, embedding=embedding)
                return result.single() is not None
            except Exception as e:
                print(f"임베딩 저장 실패: {e}")
                return False
    
    def embed_batch(
        self, 
        texts_and_ids: list[tuple[str, str]],
        progress_callback: Optional[callable] = None
    ) -> int:
        """
        여러 텍스트를 일괄 임베딩합니다.
        
        Args:
            texts_and_ids: (텍스트, evidence_id) 튜플 리스트
            progress_callback: 진행률 콜백
            
        Returns:
            성공적으로 저장된 임베딩 수
        """
        # 배치 임베딩 생성
        texts = [t[0] for t in texts_and_ids]
        try:
            embeddings = self.embeddings.embed_documents(texts)
        except Exception as e:
            print(f"배치 임베딩 생성 실패: {e}")
            return 0
        
        # 각 임베딩 저장
        stored = 0
        total = len(texts_and_ids)
        
        for i, ((text, evidence_id), embedding) in enumerate(zip(texts_and_ids, embeddings)):
            query = """
            MATCH (e:Evidence {id: $id})
            SET e.embedding = $embedding
            RETURN e.id
            """
            
            with self.client.session() as session:
                try:
                    result = session.run(query, id=evidence_id, embedding=embedding)
                    if result.single():
                        stored += 1
                except Exception as e:
                    print(f"임베딩 저장 실패 ({evidence_id}): {e}")
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return stored
    
    def similarity_search(
        self, 
        query_text: str, 
        top_k: int = TOP_K_RESULTS
    ) -> list[dict]:
        """
        쿼리 텍스트와 유사한 Evidence 노드를 검색합니다.
        
        Args:
            query_text: 검색 쿼리
            top_k: 반환할 최대 결과 수
            
        Returns:
            가장 유사한 Evidence 노드 리스트 (score 포함)
        """
        # 쿼리 임베딩 생성
        try:
            query_embedding = self.embeddings.embed_query(query_text)
        except Exception as e:
            print(f"쿼리 임베딩 생성 실패: {e}")
            return []
        
        # Neo4j Vector 검색
        query = f"""
        CALL db.index.vector.queryNodes('{self.INDEX_NAME}', $top_k, $embedding)
        YIELD node, score
        RETURN 
            node.id as id,
            node.text as text,
            node.source_doc as source_doc,
            node.page_num as page_num,
            score
        ORDER BY score DESC
        """
        
        with self.client.session() as session:
            try:
                result = session.run(query, top_k=top_k, embedding=query_embedding)
                return [dict(record) for record in result]
            except Exception as e:
                print(f"유사도 검색 실패: {e}")
                return []
    
    def close(self):
        """리소스 정리"""
        self.client.close()


if __name__ == "__main__":
    # 테스트
    print("=== Vector Store 테스트 (Gemini Embedding) ===\n")
    
    try:
        # 임베딩 테스트
        embedder = GeminiEmbeddings()
        test_text = "수자원 관리 및 물 리스크"
        embedding = embedder.embed_query(test_text)
        print(f"✓ Gemini 임베딩 테스트 성공")
        print(f"  - 입력: {test_text}")
        print(f"  - 출력 차원: {len(embedding)}")
        
    except ValueError as e:
        print(f"설정 오류: {e}")
    except Exception as e:
        print(f"오류: {e}")
