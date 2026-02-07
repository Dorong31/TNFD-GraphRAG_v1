"""
텍스트 청킹 모듈

PDF에서 추출한 텍스트를 LLM 처리와 검색에 적합한 크기의 청크로 분할합니다.
Semantic Chunking과 Fixed-size Chunking을 지원합니다.
"""

from typing import Optional
import re
from src.config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_by_size(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """
    고정 크기로 텍스트를 청킹합니다.
    
    문장 단위로 분할하면서 지정된 크기에 맞게 청크를 생성합니다.
    청크 간에 오버랩을 두어 문맥이 끊기지 않도록 합니다.
    
    Args:
        text: 분할할 텍스트
        chunk_size: 청크 최대 크기 (문자 수)
        chunk_overlap: 청크 간 오버랩 크기 (문자 수)
        
    Returns:
        청크 문자열 리스트
    """
    if not text or len(text.strip()) == 0:
        return []
    
    # 문장 단위로 분할 (마침표, 물음표, 느낌표 기준)
    # 한국어와 영어 문장 모두 지원
    sentences = re.split(r'(?<=[.!?。])\s+', text.strip())
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        sentence_length = len(sentence)
        
        # 현재 청크에 문장을 추가했을 때 크기 초과 여부 확인
        if current_length + sentence_length > chunk_size and current_chunk:
            # 현재 청크 저장
            chunks.append(" ".join(current_chunk))
            
            # 오버랩 처리: 마지막 몇 문장을 다음 청크로 이월
            overlap_sentences = []
            overlap_length = 0
            for s in reversed(current_chunk):
                if overlap_length + len(s) <= chunk_overlap:
                    overlap_sentences.insert(0, s)
                    overlap_length += len(s)
                else:
                    break
            
            current_chunk = overlap_sentences
            current_length = overlap_length
        
        current_chunk.append(sentence)
        current_length += sentence_length
    
    # 마지막 청크 저장
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks


def chunk_by_paragraph(text: str, min_chunk_size: int = 200) -> list[str]:
    """
    문단(paragraph) 단위로 텍스트를 청킹합니다.
    
    빈 줄을 기준으로 문단을 분리하고, 너무 짧은 문단은 병합합니다.
    
    Args:
        text: 분할할 텍스트
        min_chunk_size: 최소 청크 크기 (이보다 짧으면 다음 문단과 병합)
        
    Returns:
        청크 문자열 리스트
    """
    if not text or len(text.strip()) == 0:
        return []
    
    # 빈 줄(2개 이상의 연속 줄바꿈)을 기준으로 문단 분리
    paragraphs = re.split(r'\n\s*\n', text.strip())
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        if len(current_chunk) + len(para) < min_chunk_size:
            # 현재 청크에 추가
            current_chunk = f"{current_chunk}\n\n{para}" if current_chunk else para
        else:
            # 현재 청크 저장하고 새 청크 시작
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = para
    
    # 마지막 청크 저장
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def create_chunks_from_pages(
    pages: list[dict],
    chunk_method: str = "size",
    **kwargs
) -> list[dict]:
    """
    PDF 페이지 리스트에서 청크를 생성합니다.
    
    각 청크에 출처 정보(페이지 번호, 문서명)를 포함합니다.
    
    Args:
        pages: pdf_loader.load_pdf()의 반환값
        chunk_method: 청킹 방법 ("size" 또는 "paragraph")
        **kwargs: 청킹 함수에 전달할 추가 인자
        
    Returns:
        청크 정보 딕셔너리 리스트:
        - text: 청크 텍스트
        - page_num: 출처 페이지 번호
        - source_doc: 출처 문서명
        - chunk_index: 청크 인덱스 (전체 문서 기준)
    """
    all_chunks = []
    chunk_index = 0
    
    for page in pages:
        page_text = page.get("text", "")
        page_num = page.get("page_num", 0)
        source_doc = page.get("source_doc", "")
        
        # 선택한 방법으로 청킹
        if chunk_method == "paragraph":
            chunks = chunk_by_paragraph(page_text, **kwargs)
        else:  # default: size
            chunks = chunk_by_size(page_text, **kwargs)
        
        # 청크에 메타데이터 추가
        for chunk_text in chunks:
            all_chunks.append({
                "text": chunk_text,
                "page_num": page_num,
                "source_doc": source_doc,
                "chunk_index": chunk_index,
            })
            chunk_index += 1
    
    return all_chunks


if __name__ == "__main__":
    # 테스트
    sample_text = """
    Samsung Electronics is implementing water recycling programs across its facilities.
    The company faces significant water stress risks in its Vietnam operations.
    
    Climate change poses both physical and transition risks to our business.
    We are committed to reducing our environmental footprint through regenerative practices.
    
    Our sustainability report outlines key actions taken in 2024.
    These include renewable energy adoption and biodiversity conservation efforts.
    """
    
    print("=== Fixed-size Chunking ===")
    chunks = chunk_by_size(sample_text, chunk_size=200, chunk_overlap=50)
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1} ({len(chunk)} chars):")
        print(f"  {chunk[:100]}...")
    
    print("\n=== Paragraph Chunking ===")
    chunks = chunk_by_paragraph(sample_text, min_chunk_size=100)
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1} ({len(chunk)} chars):")
        print(f"  {chunk[:100]}...")
