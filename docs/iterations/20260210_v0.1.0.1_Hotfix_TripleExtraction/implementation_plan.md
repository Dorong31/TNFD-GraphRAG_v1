# Implementation Plan - Triple Extraction Hotfix

## Problem
During the Triple Extraction phase (Step 3) of the pipeline, a `TypeError: expected string or bytes-like object, got 'list'` occurred.
This was caused by the Google Gemini LLM occasionally returning a list of strings instead of a single string in `response.content`, causing `re.search` to fail in `TripleExtractor._parse_json_response`.

## Solution
Modify `src/extraction/extractor.py` to check the type of `response.content` from the LLM. If it is a list, join the elements into a single string before processing.

## Steps
1.  **Reproduce Error**: Created `debug_reproduce_2.py` to confirm that passing a list to `re.search` causes the exact TypeError.
2.  **Apply Fix**: Updated `TripleExtractor.extract` method in `src/extraction/extractor.py`.
    - Added a check: `if isinstance(result_text, list): result_text = "".join([str(item) for item in result_text])`
3.  **Verify**:
    - Re-ran the pipeline with the Samsung Biologics PDF.
    - Confirmed that Step 3 proceeds without crashing.
    - Verified graph data generation in Neo4j Browser.

## Files Modified
- `src/extraction/extractor.py`

## User Instructions
- No changes in usage. Run the pipeline as usual.
- If using Docker, ensure the Neo4j container is running.
