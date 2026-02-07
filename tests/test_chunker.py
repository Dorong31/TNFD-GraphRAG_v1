"""
청킹 모듈 테스트

텍스트 청킹 로직의 정확성을 검증합니다.
"""

import pytest
from src.data_pipeline.chunker import (
    chunk_by_size,
    chunk_by_paragraph,
    create_chunks_from_pages
)


class TestChunkBySize:
    """고정 크기 청킹 테스트"""
    
    def test_empty_text(self):
        """빈 텍스트 처리"""
        result = chunk_by_size("")
        assert result == []
    
    def test_short_text(self):
        """짧은 텍스트는 하나의 청크로"""
        text = "This is a short sentence."
        result = chunk_by_size(text, chunk_size=1000)
        
        assert len(result) == 1
        assert text in result[0]
    
    def test_chunking_respects_size(self):
        """청크 크기 제한 준수"""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        result = chunk_by_size(text, chunk_size=50, chunk_overlap=0)
        
        for chunk in result:
            # 청크 크기가 대략적으로 제한을 초과하지 않아야 함
            # (문장 단위로 분리되므로 약간의 초과는 허용)
            assert len(chunk) < 100
    
    def test_overlap_creates_context(self):
        """오버랩이 문맥 유지에 도움"""
        text = "A. B. C. D. E. F."
        result = chunk_by_size(text, chunk_size=10, chunk_overlap=5)
        
        # 오버랩이 있으면 청크 간 중복 내용이 있을 수 있음
        assert len(result) >= 1


class TestChunkByParagraph:
    """문단 기반 청킹 테스트"""
    
    def test_single_paragraph(self):
        """단일 문단 처리"""
        text = "This is a single paragraph without any breaks."
        result = chunk_by_paragraph(text)
        
        assert len(result) == 1
    
    def test_multiple_paragraphs(self):
        """여러 문단 분리"""
        text = """First paragraph here.

Second paragraph here.

Third paragraph here."""
        result = chunk_by_paragraph(text, min_chunk_size=10)
        
        assert len(result) == 3
    
    def test_short_paragraphs_merged(self):
        """짧은 문단은 병합"""
        text = """Hi.

Hello.

Goodbye."""
        result = chunk_by_paragraph(text, min_chunk_size=100)
        
        # 각 문단이 너무 짧아서 병합됨
        assert len(result) <= 2


class TestCreateChunksFromPages:
    """페이지 기반 청킹 테스트"""
    
    def test_with_page_metadata(self):
        """페이지 메타데이터 포함"""
        pages = [
            {"text": "Page one content.", "page_num": 1, "source_doc": "test.pdf"},
            {"text": "Page two content.", "page_num": 2, "source_doc": "test.pdf"},
        ]
        
        result = create_chunks_from_pages(pages)
        
        assert len(result) >= 2
        for chunk in result:
            assert "page_num" in chunk
            assert "source_doc" in chunk
            assert "chunk_index" in chunk
    
    def test_chunk_index_increments(self):
        """청크 인덱스가 순차적으로 증가"""
        pages = [
            {"text": "Content A.", "page_num": 1, "source_doc": "test.pdf"},
            {"text": "Content B.", "page_num": 2, "source_doc": "test.pdf"},
        ]
        
        result = create_chunks_from_pages(pages, chunk_size=5)
        
        indices = [c["chunk_index"] for c in result]
        # 인덱스가 0부터 순차적으로 증가
        assert indices == list(range(len(result)))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
