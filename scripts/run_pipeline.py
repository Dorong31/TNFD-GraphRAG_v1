
import os
import sys
import json
import argparse
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data_pipeline.pdf_loader import load_pdf
from src.data_pipeline.chunker import create_chunks_from_pages
from src.extraction.extractor import extract_from_chunks

def run_pipeline(pdf_path, output_dir, limit=None):
    print(f"Loading PDF from {pdf_path}...")
    try:
        pages = load_pdf(pdf_path)
    except Exception as e:
        print(f"Error loading PDF: {e}")
        return

    print(f"Loaded {len(pages)} pages.")

    print("Chunking pages...")
    chunks = create_chunks_from_pages(pages)
    print(f"Created {len(chunks)} chunks.")

    if limit:
        print(f"Limiting to first {limit} chunks for testing.")
        chunks = chunks[:limit]

    print("Extracting triples...")
    results = extract_from_chunks(chunks)
    
    # Serialize results to JSON
    output_data = []
    for res in results:
        # Convert Pydantic models to dicts
        nodes_data = [node.model_dump() for node in res.nodes]
        rels_data = [rel.model_dump() for rel in res.relationships]
        
        output_data.append({
            "source_evidence_id": res.source_evidence_id,
            "nodes": nodes_data,
            "relationships": rels_data
        })

    # Save to file
    output_path = Path(output_dir) / f"{Path(pdf_path).stem}_extraction.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"Extraction complete. Results saved to {output_path}")
    
    # Print summary
    total_nodes = sum(len(res.nodes) for res in results)
    total_rels = sum(len(res.relationships) for res in results)
    print(f"Total Nodes Extracted: {total_nodes}")
    print(f"Total Relationships Extracted: {total_rels}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run TNFD GraphRAG Extraction Pipeline")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--limit", type=int, help="Limit number of chunks to process (for testing)")
    parser.add_argument("--output", default="output", help="Output directory")
    
    args = parser.parse_args()
    
    run_pipeline(args.pdf_path, args.output, args.limit)
