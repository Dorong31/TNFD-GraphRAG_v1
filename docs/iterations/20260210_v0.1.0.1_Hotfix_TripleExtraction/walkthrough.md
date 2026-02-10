# Walkthrough - Triple Extraction Hotfix (v0.1.0.1)

This walkthrough documents the changes made to fix a critical error in the Triple Extraction step of the TNFD-GraphRAG pipeline.

## Changes

### 1. `src/extraction/extractor.py`

- Modified `TripleExtractor.extract` method.
- Added a type check for `response.content` returned by `ChatGoogleGenerativeAI`.
- If the content is a list (which happens occasionally with Gemini), it is now joined into a single string.

```python
# Before
response = self.llm.invoke([HumanMessage(content=prompt)])
result_text = response.content

# After
response = self.llm.invoke([HumanMessage(content=prompt)])
result_text = response.content
# Google Gemini가 가끔 리스트 형태의 콘텐츠를 반환하는 경우 처리
if isinstance(result_text, list):
    result_text = "".join([str(item) for item in result_text])
```

## Verification Results

- **Environment**: Docker (Neo4j 5.26-community), Python 3.1x
- **Test File**: `data/pdfs/207940_삼성바이오로직스_2025_KR.pdf` (224 pages)
- **Result**:
  - **Step 1 (Load)**: Success (224 pages)
  - **Step 2 (Chunk)**: Success (428 chunks)
  - **Step 3 (Extract)**: Previously failed with TypeError, now running successfully.
  - **Neo4j Data**: Validated that nodes and relationships are being created in the graph database.
