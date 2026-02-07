"""
PDF 로드 및 파싱 모듈

PyMuPDF4LLM을 사용하여 PDF 문서를 LLM 처리에 적합한 형태로 변환합니다.
각 페이지별 텍스트와 메타데이터를 추출합니다.
"""

from pathlib import Path
from typing import Optional
import pymupdf4llm
import pymupdf  # 페이지 수 확인용


def load_pdf(pdf_path: str | Path) -> list[dict]:
    """
    PDF 파일을 로드하고 페이지별 텍스트를 추출합니다.
    
    Args:
        pdf_path: PDF 파일 경로
        
    Returns:
        페이지별 정보를 담은 딕셔너리 리스트
        각 딕셔너리는 다음 키를 포함:
        - text: 페이지 텍스트 (Markdown 형식)
        - page_num: 페이지 번호 (1부터 시작)
        - source_doc: 원본 파일명
        
    Raises:
        FileNotFoundError: PDF 파일이 존재하지 않는 경우
        ValueError: PDF 파일을 읽을 수 없는 경우
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
    
    if not pdf_path.suffix.lower() == '.pdf':
        raise ValueError(f"PDF 파일이 아닙니다: {pdf_path}")
    
    # pymupdf4llm을 사용하여 PDF를 Markdown 형식으로 변환
    # 페이지별로 분리하여 추출
    try:
        # 페이지별 Markdown 추출
        pages_md = pymupdf4llm.to_markdown(
            str(pdf_path),
            page_chunks=True,  # 페이지별로 분리
        )
    except Exception as e:
        raise ValueError(f"PDF 파일을 읽는 중 오류 발생: {e}")
    
    # 결과 구조화
    result = []
    for i, page_data in enumerate(pages_md):
        result.append({
            "text": page_data.get("text", ""),
            "page_num": i + 1,  # 1-indexed
            "source_doc": pdf_path.name,
            "metadata": page_data.get("metadata", {}),
        })
    
    return result


def load_pdf_as_single_text(pdf_path: str | Path) -> str:
    """
    PDF 파일 전체를 하나의 텍스트로 로드합니다.
    
    Args:
        pdf_path: PDF 파일 경로
        
    Returns:
        전체 PDF 내용을 담은 문자열 (Markdown 형식)
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
    
    return pymupdf4llm.to_markdown(str(pdf_path))


def get_pdf_info(pdf_path: str | Path) -> dict:
    """
    PDF 파일의 기본 정보를 반환합니다.
    
    Args:
        pdf_path: PDF 파일 경로
        
    Returns:
        PDF 정보 딕셔너리:
        - filename: 파일명
        - page_count: 총 페이지 수
        - title: 문서 제목 (있는 경우)
        - author: 작성자 (있는 경우)
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
    
    with pymupdf.open(str(pdf_path)) as doc:
        metadata = doc.metadata
        return {
            "filename": pdf_path.name,
            "page_count": len(doc),
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "creation_date": metadata.get("creationDate", ""),
        }


if __name__ == "__main__":
    # 사용 예시
    import sys
    
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        print(f"=== PDF 정보: {pdf_file} ===")
        
        try:
            info = get_pdf_info(pdf_file)
            print(f"  파일명: {info['filename']}")
            print(f"  페이지 수: {info['page_count']}")
            print(f"  제목: {info['title'] or '(없음)'}")
            
            print("\n=== 첫 페이지 미리보기 ===")
            pages = load_pdf(pdf_file)
            if pages:
                preview = pages[0]["text"][:500]
                print(preview + "..." if len(pages[0]["text"]) > 500 else preview)
        except Exception as e:
            print(f"오류: {e}")
    else:
        print("사용법: python pdf_loader.py <PDF파일경로>")
