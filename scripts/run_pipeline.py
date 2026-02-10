"""
TNFD-GraphRAG 추출 파이프라인 스크립트

PDF 문서에서 Knowledge Graph Triple을 추출합니다.
진행률 표시, 중간 저장, 재개 기능을 지원합니다.

사용 예시:
  # 전체 파이프라인 실행
  python scripts/run_pipeline.py data/pdfs/report.pdf

  # 처음 5개 청크만 테스트
  python scripts/run_pipeline.py data/pdfs/report.pdf --limit 5

  # 10번째 청크부터 시작 (이전 실행 이어서)
  python scripts/run_pipeline.py data/pdfs/report.pdf --start 10

  # 20~30번 청크만 처리
  python scripts/run_pipeline.py data/pdfs/report.pdf --start 20 --limit 10
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

# src 패키지를 import 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from src.data_pipeline.pdf_loader import load_pdf
from src.data_pipeline.chunker import create_chunks_from_pages
from src.extraction.extractor import TripleExtractor


def save_results(results, output_path):
    """
    추출 결과를 JSON 파일로 저장합니다.
    
    Args:
        results: ExtractionResult 리스트
        output_path: 저장할 파일 경로
    """
    output_data = []
    for res in results:
        # Pydantic 모델을 딕셔너리로 변환
        nodes_data = [node.model_dump() for node in res.nodes]
        rels_data = [rel.model_dump() for rel in res.relationships]
        
        output_data.append({
            "source_evidence_id": res.source_evidence_id,
            "nodes": nodes_data,
            "relationships": rels_data
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)


def run_pipeline(pdf_path, output_dir, limit=None, start=0):
    """
    PDF에서 Triple 추출 파이프라인을 실행합니다.
    
    Args:
        pdf_path: PDF 파일 경로
        output_dir: 결과 저장 디렉토리
        limit: 처리할 최대 청크 수 (None이면 전체)
        start: 시작할 청크 인덱스 (0부터)
    """
    pdf_stem = Path(pdf_path).stem
    
    # ====== 1단계: PDF 로드 ======
    print(f"📄 PDF 로드 중... ({pdf_path})")
    try:
        pages = load_pdf(pdf_path)
    except Exception as e:
        print(f"❌ PDF 로드 실패: {e}")
        return

    print(f"   ✓ {len(pages)} 페이지 로드 완료")

    # ====== 2단계: 텍스트 청킹 ======
    print(f"📝 텍스트 청킹 중...")
    chunks = create_chunks_from_pages(pages)
    total_chunks = len(chunks)
    print(f"   ✓ {total_chunks} 청크 생성 완료")

    # 시작/제한 범위 적용
    end = total_chunks
    if limit:
        end = min(start + limit, total_chunks)
    
    chunks = chunks[start:end]
    process_count = len(chunks)
    
    if start > 0 or limit:
        print(f"   → 청크 범위: [{start}:{end}] ({process_count}개 처리)")

    # ====== 3단계: Triple 추출 ======
    print(f"\n🔍 Triple 추출 시작...")
    print(f"   (LLM API를 호출하므로 시간이 소요됩니다)")
    print(f"   {'─' * 50}")
    
    extractor = TripleExtractor()
    results = []
    start_time = time.time()
    
    # 중간 저장 경로 설정
    output_path = Path(output_dir) / f"{pdf_stem}_extraction.json"
    partial_path = Path(output_dir) / f"{pdf_stem}_extraction_partial.json"
    
    for i, chunk in enumerate(chunks):
        chunk_start = time.time()
        global_idx = start + i  # 전체 기준 인덱스
        
        # 진행률 표시
        elapsed = time.time() - start_time
        if i > 0:
            avg_per_chunk = elapsed / i
            remaining = avg_per_chunk * (process_count - i)
            eta_str = f"남은 예상: {remaining/60:.1f}분"
        else:
            eta_str = "계산 중..."
        
        print(f"   [{i+1}/{process_count}] 청크 #{global_idx} "
              f"(p.{chunk.get('page_num', '?')}) 처리 중... ", end="", flush=True)
        
        # 추출 실행
        result = extractor.extract(
            text=chunk.get("text", ""),
            source_doc=chunk.get("source_doc", ""),
            page_num=chunk.get("page_num", 0),
            chunk_index=chunk.get("chunk_index", i)
        )
        results.append(result)
        
        # 결과 요약 출력
        chunk_time = time.time() - chunk_start
        node_count = len(result.nodes)
        rel_count = len(result.relationships)
        print(f"노드 {node_count}, 관계 {rel_count} "
              f"({chunk_time:.1f}초) | {eta_str}")
        
        # 매 청크마다 중간 저장 (crash 방지)
        save_results(results, partial_path)

    # ====== 4단계: 최종 저장 ======
    elapsed_total = time.time() - start_time
    
    # 최종 파일로 저장
    save_results(results, output_path)
    
    # 중간 저장 파일 삭제
    if partial_path.exists():
        partial_path.unlink()

    # ====== 완료 요약 ======
    print(f"\n{'═' * 50}")
    print(f"✅ 추출 완료!")
    print(f"{'═' * 50}")
    
    total_nodes = sum(len(res.nodes) for res in results)
    total_rels = sum(len(res.relationships) for res in results)
    empty_chunks = sum(1 for res in results if len(res.nodes) == 0)
    
    print(f"   📊 총 노드: {total_nodes}")
    print(f"   📊 총 관계: {total_rels}")
    print(f"   📊 빈 청크: {empty_chunks}/{process_count}")
    print(f"   ⏱️  소요 시간: {elapsed_total/60:.1f}분 "
          f"(청크 평균: {elapsed_total/max(process_count, 1):.1f}초)")
    print(f"   💾 결과 저장: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TNFD-GraphRAG Triple 추출 파이프라인",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python scripts/run_pipeline.py data/pdfs/report.pdf
  python scripts/run_pipeline.py data/pdfs/report.pdf --limit 5
  python scripts/run_pipeline.py data/pdfs/report.pdf --start 10 --limit 5
        """
    )
    parser.add_argument("pdf_path", help="처리할 PDF 파일 경로")
    parser.add_argument("--limit", type=int, help="처리할 최대 청크 수 (테스트용)")
    parser.add_argument("--start", type=int, default=0, help="시작할 청크 인덱스 (기본: 0)")
    parser.add_argument("--output", default="output", help="결과 저장 디렉토리 (기본: output)")
    
    args = parser.parse_args()
    
    run_pipeline(args.pdf_path, args.output, args.limit, args.start)
