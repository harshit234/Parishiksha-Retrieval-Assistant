"""
chunking.py — Token-aware chunker with content_type and page metadata.

Upgrade notes:
- Token count estimated via: len(content.split()) * 1.3 (approximation without a tokenizer)
- content_type auto-detected from heuristics: 'equation', 'example', 'law', 'list', 'definition', 'application', 'concept'
- page metadata preserved from per-file page maps (extend as more docs are added)
"""

import json
import os
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi


# ---------------------------------------------------------------------------
# Page-range map: maps each source file to the PDF page range it covers.
# Update this when new chapters/files are added.
# ---------------------------------------------------------------------------
SOURCE_PAGE_MAP = {
    "motion_ch8.txt": {
        "chapter": "Motion",
        "chapter_number": 8,
        "textbook": "NCERT Science Class 9",
        "page_start": 100,
        "page_end": 118,
    },
    "force_ch9.txt": {
        "chapter": "Force and Laws of Motion",
        "chapter_number": 9,
        "textbook": "NCERT Science Class 9",
        "page_start": 118,
        "page_end": 131,
    },
}


def _estimate_tokens(text: str) -> int:
    """Rough token count: word count × 1.3 (accounts for punctuation tokens)."""
    return int(len(text.split()) * 1.3)


def _detect_content_type(text: str) -> str:
    """
    Heuristically classify a chunk into one of:
      equation | example | law | list | definition | application | concept
    """
    t = text.lower()
    if re.search(r"example|solution|given:|find:|using [vusf]", t):
        return "example"
    if re.search(r"law of|first law|second law|third law|newton", t):
        return "law"
    if re.search(r"v\s*=\s*u|f\s*=\s*m|s\s*=\s*u|v²|equation of motion", t):
        return "equation"
    if re.search(r"application|used in|real.life|example:|e\.g\.", t):
        return "application"
    if re.search(r"definition|is defined|what is|refers to|means", t):
        return "definition"
    # numbered/bulleted list with multiple items
    if len(re.findall(r"^\s*[-\d]\.", text, re.MULTILINE)) >= 2 or len(re.findall(r"^\s*-", text, re.MULTILINE)) >= 3:
        return "list"
    return "concept"


def _detect_topic(text: str) -> str:
    """Lightweight keyword-based topic tagger."""
    t = text.lower()
    if "friction" in t:
        return "friction"
    if "momentum" in t and "conservation" in t:
        return "conservation of momentum"
    if "momentum" in t:
        return "momentum"
    if "impulse" in t:
        return "impulse"
    if "third law" in t or "action.*reaction" in t:
        return "newton's third law"
    if "second law" in t or "f = ma" in t or "f=ma" in t:
        return "newton's second law"
    if "first law" in t or "inertia" in t:
        return "newton's first law"
    if "equation of motion" in t or re.search(r"v\s*=\s*u\s*\+\s*at", t):
        return "equations of motion"
    if "circular motion" in t:
        return "uniform circular motion"
    if "acceleration" in t:
        return "acceleration"
    if "velocity" in t or "speed" in t:
        return "speed and velocity"
    if "displacement" in t or "distance" in t:
        return "distance and displacement"
    if "weight" in t and "mass" in t:
        return "mass and weight"
    if "force" in t:
        return "force"
    if "motion" in t:
        return "motion basics"
    return "general"


def _estimate_page(chunk_index: int, total_chunks: int, page_start: int, page_end: int):
    """Linearly interpolate a page number for a chunk within its source file."""
    if total_chunks <= 1:
        return page_start, page_end
    fraction = chunk_index / max(total_chunks - 1, 1)
    page_range = page_end - page_start
    estimated = page_start + int(fraction * page_range)
    return estimated, min(estimated + 1, page_end)


def create_chunks(
    files: list[str] | None = None,
    chunk_size: int = 512,
    chunk_overlap: int = 128,
) -> list[dict]:
    """
    Read source text files, split into overlapping chunks, and annotate with:
      - token_count
      - content_type
      - topic
      - chapter / chapter_number / textbook
      - page_start / page_end (estimated)
      - source filename
      - has_formula flag
    """
    if files is None:
        files = [
            "data/processed/motion_ch8.txt",
            "data/processed/force_ch9.txt",
        ]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    all_chunks: list[dict] = []
    global_id = 0

    for file_path in files:
        source_name = os.path.basename(file_path)
        meta_template = SOURCE_PAGE_MAP.get(source_name, {
            "chapter": "Unknown",
            "chapter_number": 0,
            "textbook": "Unknown",
            "page_start": 1,
            "page_end": 1,
        })

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        raw_chunks = splitter.split_text(text)
        total = len(raw_chunks)

        for local_idx, chunk_text in enumerate(raw_chunks):
            p_start, p_end = _estimate_page(
                local_idx, total,
                meta_template["page_start"],
                meta_template["page_end"],
            )
            content_type = _detect_content_type(chunk_text)
            topic = _detect_topic(chunk_text)
            has_formula = bool(re.search(
                r"=\s*[a-zA-Z0-9]+|[a-zA-Z]\s*[²³]|[Ff]\s*=|[Vv]\s*=|[Ss]\s*=|μ|Δ|∑",
                chunk_text,
            ))

            all_chunks.append({
                "id": global_id,
                "content": chunk_text,
                "token_count": _estimate_tokens(chunk_text),
                "metadata": {
                    "source": source_name,
                    "chapter": meta_template["chapter"],
                    "chapter_number": meta_template["chapter_number"],
                    "topic": topic,
                    "content_type": content_type,
                    "page_start": p_start,
                    "page_end": p_end,
                    "textbook": meta_template["textbook"],
                    "has_formula": has_formula,
                },
            })
            global_id += 1

    print(f"✓ Created {len(all_chunks)} chunks from {len(files)} file(s)")
    return all_chunks


def save_chunks(chunks: list[dict], path: str = "data/processed/chunks.json") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    total_tokens = sum(c["token_count"] for c in chunks)
    print(f"✓ Saved {len(chunks)} chunks → {path}  (total ≈{total_tokens} tokens)")


def load_chunks(path: str = "data/processed/chunks.json") -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"✓ Loaded {len(chunks)} chunks from {path}")
    return chunks


def build_bm25_index(chunks: list[dict]):
    """Build a BM25 index over chunk content for sparse retrieval."""
    tokenized = [re.findall(r"\w+", c["content"].lower()) for c in chunks]
    bm25 = BM25Okapi(tokenized)
    print(f"✓ BM25 index built over {len(chunks)} chunks")
    return bm25


if __name__ == "__main__":
    chunks = create_chunks()
    save_chunks(chunks)
    chunks = load_chunks()
    bm25 = build_bm25_index(chunks)
