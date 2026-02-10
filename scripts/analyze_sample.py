
import sys
import json
import pymupdf
import pymupdf4llm
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data_pipeline.chunker import create_chunks_from_pages
from src.extraction.extractor import extract_from_chunks

def analyze_sample(pdf_path, num_pages=10, output_dir="output"):
    print(f"Analyzing first {num_pages} pages of {pdf_path}...")
    
    # 1. Load specific pages using pymupdf4llm
    try:
        # standard pymupdf open to get page count if needed, but to_markdown accepts path
        # actually to_markdown accepts path or document. 
        # let's use path and pages argument
        md_text = pymupdf4llm.to_markdown(str(pdf_path), pages=list(range(num_pages)), page_chunks=True)
    except Exception as e:
        print(f"Error loading PDF: {e}")
        return

    # 2. Convert to our internal format
    pages = []
    for i, page_data in enumerate(md_text):
        pages.append({
            "text": page_data.get("text", ""),
            "page_num": i + 1,
            "source_doc": Path(pdf_path).name,
            "metadata": page_data.get("metadata", {})
        })
        
    print(f"Loaded {len(pages)} pages.")

    # 3. Chunk
    chunks = create_chunks_from_pages(pages)
    print(f"Created {len(chunks)} chunks.")

    # 4. Extract
    print("Extracting triples...")
    # results = extract_from_chunks(chunks)
    
    # Use direct extractor with progress
    from src.extraction.extractor import TripleExtractor
    extractor = TripleExtractor()
    
    def progress_callback(current, total):
        print(f"  Processed {current}/{total} chunks...")
        
    results = extractor.extract_batch(chunks, progress_callback=progress_callback)
    
    # 5. Save
    output_data = []
    for res in results:
        nodes_data = [node.model_dump() for node in res.nodes]
        rels_data = [rel.model_dump() for rel in res.relationships]
        
        output_data.append({
            "source_evidence_id": res.source_evidence_id,
            "nodes": nodes_data,
            "relationships": rels_data
        })

    output_path = Path(output_dir) / f"{Path(pdf_path).stem}_sample_analysis.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"Sample analysis complete. Saved to {output_path}")
    
    # Summary
    total_nodes = sum(len(res.nodes) for res in results)
    total_rels = sum(len(res.relationships) for res in results)
    print(f"Total Nodes: {total_nodes}")
    print(f"Total Relationships: {total_rels}")
    
    # Show some examples
    if results:
        print("\n--- Extracted Data Preview ---")
        first_res = results[0]
        for node in first_res.nodes[:3]:
           print(f"Node: {node.name} ({node.node_type})")
        for rel in first_res.relationships[:3]:
           print(f"Rel: {rel.source_id} -[{rel.relationship_type}]-> {rel.target_id}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_sample.py <pdf_path> [num_pages]")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    num_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    analyze_sample(pdf_path, num_pages)
