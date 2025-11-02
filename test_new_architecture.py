#!/usr/bin/env python3
"""End-to-end smoke test for the modern pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Ensure backend package is importable when run from repo root
sys.path.insert(0, str(ROOT))

from backend.services.advanced_parser import LegalDocumentParser
from backend.services.knowledge_indexer import KnowledgeIndexer
from backend.services.legal_ai_service import LegalAIService


def ensure_sample_docs(doc_dir: Path) -> None:
    """Create a handful of lightweight sample documents if needed."""
    doc_dir.mkdir(parents=True, exist_ok=True)

    if any(doc_dir.glob("*.txt")):
        return

    samples = {
        "sample_contract.txt": [
            "MASTER SERVICES AGREEMENT",
            "This Services Agreement is entered into between Apex Systems LLC and Summit Partners Inc.",
            "Non-compete. The Provider agrees not to engage with direct competitors in California for 18 months.",
            "Termination. Either party may terminate with ninety (90) days notice.",
        ],
        "nda_template.txt": [
            "MUTUAL NON-DISCLOSURE AGREEMENT",
            "Confidential Information includes product roadmaps, pricing, and customer lists.",
            "Governing Law. This agreement is governed by the laws of the State of New York.",
        ],
        "employment_policy.txt": [
            "EMPLOYEE HANDBOOK",
            "Equal Opportunity. The Company provides equal employment opportunity to all employees.",
            "Arbitration. Disputes shall be resolved through binding arbitration in Texas.",
        ],
    }

    for filename, lines in samples.items():
        (doc_dir / filename).write_text("\n\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--docs",
        type=Path,
        default=ROOT / "data" / "sample_docs",
        help="Folder containing test documents (default: data/sample_docs)",
    )
    args = parser.parse_args()

    ensure_sample_docs(args.docs)

    print("=" * 60)
    print("OnMyPC Legal AI - Pipeline Smoke Test")
    print("=" * 60)

    parser_service = LegalDocumentParser()
    indexer = KnowledgeIndexer()

    first_file = next(args.docs.glob("*.txt"))
    print(f"\n[Test 1] Parsing document: {first_file.name}")
    parsed_doc = parser_service.parse_document(first_file)
    print(f"  Title     : {parsed_doc.title}")
    print(f"  Sections  : {parsed_doc.total_sections}")
    print(f"  Chunks    : {parsed_doc.total_chunks}")
    print(f"  Doc Type  : {parsed_doc.doctype}")
    print(f"  Jurisdiction: {parsed_doc.jurisdiction}")

    print("\n[Test 2] Indexing directory...")
    indexer.initialize_models()
    stats = indexer.index_directory(args.docs, recursive=False)
    print(f"  Status    : {stats.get('status')}")
    print(f"  Documents : {stats.get('indexed_documents')}")
    print(f"  Chunks    : {stats.get('total_chunks')}")
    print(f"  Vectors   : {stats.get('vector_index_size')}")

    print("\n[Test 3] End-to-end query...")
    service = LegalAIService()
    init = service.initialize()
    print(f"  Init status: {init.get('status')}")

    response = service.query("Find the non-compete requirements in California")
    print(f"  Results  : {len(response.results)}")
    if response.results:
        top = response.results[0]
        print(f"  Top Doc  : {top.document.title}")
        print(f"  Final Score: {top.final_score:.3f}")
        print(f"  Snippet  : {top.chunk.text[:160].replace('\\n', ' ')}...")

    print("\nSuccess! The pipeline is operational.")


if __name__ == "__main__":
    main()
