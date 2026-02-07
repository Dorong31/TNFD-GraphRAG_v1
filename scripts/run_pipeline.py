"""
전체 파이프라인 실행 스크립트

PDF 문서를 읽어 Knowledge Graph를 구축하고
질의응답을 수행하는 전체 파이프라인을 실행합니다.

사용법:
    python scripts/run_pipeline.py --pdf data/pdfs/sample.pdf
    python scripts/run_pipeline.py --query "이 기업의 주요 리스크는?"
"""

import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import validate_config
from src.data_pipeline.pdf_loader import load_pdf, get_pdf_info
from src.data_pipeline.chunker import create_chunks_from_pages
from src.extraction.extractor import TripleExtractor
from src.graph.neo4j_client import Neo4jClient
from src.graph.vector_store import VectorStore
from src.retrieval.generator import query_with_sources


def run_ingestion_pipeline(pdf_path: str, verbose: bool = True):
    """
    PDF 문서를 Knowledge Graph로 변환하는 파이프라인
    
    1. PDF 로드
    2. 텍스트 청킹
    3. Triple 추출
    4. Neo4j 저장
    5. 임베딩 생성 및 저장
    
    Args:
        pdf_path: PDF 파일 경로
        verbose: 진행 상황 출력 여부
    """
    if verbose:
        print("=" * 60)
        print("TNFD-GraphRAG Ingestion Pipeline")
        print("=" * 60)
    
    # 설정 검증
    config_status = validate_config()
    if not config_status["google_api_key"]:
        print("❌ Google API 키가 설정되지 않았습니다.")
        return False
    if not config_status["neo4j_password"]:
        print("❌ Neo4j 비밀번호가 설정되지 않았습니다.")
        return False
    
    # 1. PDF 로드
    if verbose:
        print(f"\n📄 Step 1: PDF 로드 중... ({pdf_path})")
    
    try:
        info = get_pdf_info(pdf_path)
        if verbose:
            print(f"   - 파일명: {info['filename']}")
            print(f"   - 페이지 수: {info['page_count']}")
        
        pages = load_pdf(pdf_path)
        if verbose:
            print(f"   ✓ {len(pages)} 페이지 로드 완료")
    except Exception as e:
        print(f"❌ PDF 로드 실패: {e}")
        return False
    
    # 2. 텍스트 청킹
    if verbose:
        print("\n📝 Step 2: 텍스트 청킹 중...")
    
    chunks = create_chunks_from_pages(pages, chunk_method="size")
    if verbose:
        print(f"   ✓ {len(chunks)} 청크 생성 완료")
    
    # 3. Triple 추출
    if verbose:
        print("\n🔍 Step 3: Triple 추출 중...")
        print(f"   (이 단계는 LLM API를 호출하므로 시간이 소요될 수 있습니다)")
    
    try:
        extractor = TripleExtractor()
        
        def progress_callback(current, total):
            if verbose:
                print(f"\r   진행: {current}/{total} ({100*current/total:.1f}%)", end="")
        
        extraction_results = extractor.extract_batch(chunks, progress_callback)
        
        if verbose:
            print()  # 줄바꿈
            total_nodes = sum(len(r.nodes) for r in extraction_results)
            total_rels = sum(len(r.relationships) for r in extraction_results)
            print(f"   ✓ {total_nodes} 노드, {total_rels} 관계 추출 완료")
    except Exception as e:
        print(f"\n❌ Triple 추출 실패: {e}")
        return False
    
    # 4. Neo4j 저장
    if verbose:
        print("\n💾 Step 4: Neo4j에 저장 중...")
    
    try:
        neo4j_client = Neo4jClient()
        
        nodes_created = 0
        rels_created = 0
        
        for result in extraction_results:
            stats = neo4j_client.save_extraction_result(result)
            nodes_created += stats["nodes_created"]
            rels_created += stats["relationships_created"]
        
        if verbose:
            print(f"   ✓ {nodes_created} 노드, {rels_created} 관계 저장 완료")
    except Exception as e:
        print(f"❌ Neo4j 저장 실패: {e}")
        return False
    
    # 5. 임베딩 생성 및 저장
    if verbose:
        print("\n🧠 Step 5: 임베딩 생성 및 저장 중...")
    
    try:
        vector_store = VectorStore(neo4j_client=neo4j_client)
        vector_store.create_vector_index()
        
        # Evidence 노드의 텍스트와 ID 수집
        texts_and_ids = []
        for result in extraction_results:
            for node in result.nodes:
                if hasattr(node, 'text') and hasattr(node, 'id'):
                    texts_and_ids.append((node.text, node.id))
        
        if texts_and_ids:
            stored = vector_store.embed_batch(texts_and_ids)
            if verbose:
                print(f"   ✓ {stored}/{len(texts_and_ids)} 임베딩 저장 완료")
        
        vector_store.close()
    except Exception as e:
        print(f"⚠️ 임베딩 저장 중 오류 (계속 진행): {e}")
    
    # 완료
    if verbose:
        print("\n" + "=" * 60)
        print("✅ 파이프라인 완료!")
        print("=" * 60)
        
        # 최종 통계
        stats = neo4j_client.get_statistics()
        print(f"\n📊 그래프 통계:")
        print(f"   - 총 노드 수: {stats['total_nodes']}")
        print(f"   - 총 관계 수: {stats['total_relationships']}")
        if stats['nodes_by_type']:
            print("   - 노드 타입별:")
            for t, c in stats['nodes_by_type'].items():
                print(f"       {t}: {c}")
        
        neo4j_client.close()
    
    return True


def run_query(question: str, verbose: bool = True):
    """
    질의응답 수행
    
    Args:
        question: 사용자 질문
        verbose: 상세 출력 여부
    """
    if verbose:
        print("=" * 60)
        print("TNFD-GraphRAG Query")
        print("=" * 60)
        print(f"\n📌 질문: {question}\n")
    
    try:
        result = query_with_sources(question)
        
        print("📝 답변:")
        print("-" * 40)
        print(result["answer"])
        print("-" * 40)
        
        if result["sources"]:
            print("\n📚 출처:")
            for src in result["sources"]:
                print(f"   - {src['document']}, p.{src['page']} (유사도: {src['relevance_score']:.4f})")
        
        return True
    except Exception as e:
        print(f"❌ 질의 실패: {e}")
        return False


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="TNFD-GraphRAG 파이프라인 실행",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # PDF 문서로 Knowledge Graph 구축
  python run_pipeline.py --pdf data/pdfs/sustainability_report.pdf
  
  # 질의응답 수행
  python run_pipeline.py --query "이 기업의 주요 물리적 리스크는?"
  
  # PDF 처리 후 바로 질의
  python run_pipeline.py --pdf report.pdf --query "수자원 관리 현황은?"
        """
    )
    
    parser.add_argument(
        "--pdf",
        type=str,
        help="처리할 PDF 파일 경로"
    )
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="질의할 질문"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="진행 상황 출력 최소화"
    )
    
    args = parser.parse_args()
    
    # 아무 인자도 없으면 도움말 출력
    if not args.pdf and not args.query:
        parser.print_help()
        return
    
    verbose = not args.quiet
    
    # PDF 처리
    if args.pdf:
        success = run_ingestion_pipeline(args.pdf, verbose=verbose)
        if not success:
            sys.exit(1)
        print()  # 빈 줄
    
    # 질의 처리
    if args.query:
        success = run_query(args.query, verbose=verbose)
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
