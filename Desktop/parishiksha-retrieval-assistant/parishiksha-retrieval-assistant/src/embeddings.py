"""
embeddings.py — Dense retrieval via OpenAI text-embedding-3-small + ChromaDB.

Responsibilities:
  1. build_vectorstore()  — embed all chunks and persist to a local Chroma
                            collection (idempotent: skips if already built).
  2. retrieve(query, k)   — embed a query string, run cosine similarity search,
                            return the top-k chunk dicts (same schema as chunks.json).
  3. get_vectorstore()    — lazy singleton: returns the collection, building it
                            once on first call.

Usage (standalone):
    python -m src.embeddings

Usage (imported):
    from src.embeddings import retrieve
    results = retrieve("What are Newton's laws?", k=5)
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CHUNKS_PATH    = "data/processed/chunks.json"
CHROMA_DIR     = "data/processed/chroma_db"          # persisted on disk
COLLECTION_NAME = "parishiksha_v2"
EMBED_MODEL    = "text-embedding-3-small"
EMBED_DIM      = 1536                                  # fixed for this model
BATCH_SIZE     = 64                                    # stay well under API limits

# ---------------------------------------------------------------------------
# Lazy imports for chromadb (avoid hard crash if not installed)
# ---------------------------------------------------------------------------
try:
    import chromadb
    from chromadb.config import Settings
except ImportError as exc:
    raise ImportError(
        "chromadb is not installed. Run:  pip install chromadb"
    ) from exc


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_chunks(path: str = CHUNKS_PATH) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    return chunks


def _openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. "
            "Add it to your .env file or export it as an environment variable."
        )
    return OpenAI(api_key=api_key)


def _embed_texts(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts in batches.
    Returns a flat list of embedding vectors in the same order as `texts`.
    """
    all_embeddings: list[list[float]] = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start : start + BATCH_SIZE]
        response = client.embeddings.create(model=EMBED_MODEL, input=batch)
        # response.data is sorted by index, so order is preserved
        batch_vecs = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
        all_embeddings.extend(batch_vecs)
        # Brief pause to respect rate limits on free tiers
        if start + BATCH_SIZE < len(texts):
            time.sleep(0.25)
    return all_embeddings


def _chroma_client() -> chromadb.PersistentClient:
    Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_DIR)


def _flatten_metadata(meta: dict[str, Any]) -> dict[str, Any]:
    """
    Chroma only accepts str | int | float | bool values in metadata dicts.
    This function ensures all values are one of those primitives.
    """
    flat: dict[str, Any] = {}
    for k, v in meta.items():
        if isinstance(v, (str, int, float, bool)):
            flat[k] = v
        else:
            flat[k] = str(v)
    return flat


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_vectorstore(
    chunks_path: str = CHUNKS_PATH,
    force_rebuild: bool = False,
) -> chromadb.Collection:
    """
    Embed all chunks and persist to Chroma.

    Args:
        chunks_path:    Path to chunks.json.
        force_rebuild:  If True, drop and recreate the collection even if it
                        already exists and is fully populated.

    Returns:
        The Chroma collection object.
    """
    client_chroma = _chroma_client()

    # Check if collection already exists and is populated
    existing_names = [c.name for c in client_chroma.list_collections()]
    if COLLECTION_NAME in existing_names and not force_rebuild:
        collection = client_chroma.get_collection(COLLECTION_NAME)
        count = collection.count()
        if count > 0:
            print(
                f"✓ Chroma collection '{COLLECTION_NAME}' already exists "
                f"({count} vectors). Skipping rebuild. "
                f"Pass force_rebuild=True to regenerate."
            )
            return collection

    # Drop stale collection if force_rebuild
    if COLLECTION_NAME in existing_names and force_rebuild:
        client_chroma.delete_collection(COLLECTION_NAME)
        print(f"⚠  Dropped existing collection '{COLLECTION_NAME}' for rebuild.")

    collection = client_chroma.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},          # cosine similarity
    )

    chunks = _load_chunks(chunks_path)
    openai_client = _openai_client()

    print(f"⏳ Embedding {len(chunks)} chunks with '{EMBED_MODEL}' …")
    texts = [c["content"] for c in chunks]
    embeddings = _embed_texts(openai_client, texts)
    print(f"✓ Embeddings generated ({len(embeddings)} vectors, dim={EMBED_DIM})")

    # Upsert into Chroma in one batch
    collection.add(
        ids=[str(c["id"]) for c in chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[_flatten_metadata(c.get("metadata", {})) for c in chunks],
    )

    print(
        f"✓ Persisted {collection.count()} vectors → '{CHROMA_DIR}/' "
        f"(collection: '{COLLECTION_NAME}')"
    )
    return collection


# Module-level singleton so repeated imports don't rebuild
_COLLECTION: chromadb.Collection | None = None


def get_vectorstore(force_rebuild: bool = False) -> chromadb.Collection:
    """Return the singleton Chroma collection, building it on first call."""
    global _COLLECTION
    if _COLLECTION is None or force_rebuild:
        _COLLECTION = build_vectorstore(force_rebuild=force_rebuild)
    return _COLLECTION


def retrieve(
    query: str,
    k: int = 5,
    filter_metadata: dict[str, Any] | None = None,
) -> list[dict]:
    """
    Embed `query` with text-embedding-3-small and return the top-k most
    similar chunks from Chroma as a list of dicts matching the chunks.json
    schema (with an added `_score` key showing cosine distance).

    Args:
        query:           Natural-language query string.
        k:               Number of results to return (default 5).
        filter_metadata: Optional Chroma `where` filter dict, e.g.
                         {"content_type": "example"} or
                         {"chapter_number": 8}.

    Returns:
        List of chunk dicts, ordered by relevance (most relevant first).
        Each dict contains all original metadata plus:
          - "_score": float  (cosine distance — lower is more similar)
          - "_rank":  int    (1-indexed rank in result list)
    """
    collection = get_vectorstore()
    openai_client = _openai_client()

    # Embed the query (single-text call, no batching needed)
    response = openai_client.embeddings.create(model=EMBED_MODEL, input=[query])
    query_vec = response.data[0].embedding

    # Build Chroma query kwargs
    query_kwargs: dict[str, Any] = {
        "query_embeddings": [query_vec],
        "n_results": min(k, collection.count()),
        "include": ["documents", "metadatas", "distances"],
    }
    if filter_metadata:
        query_kwargs["where"] = filter_metadata

    results = collection.query(**query_kwargs)

    # Unpack Chroma's nested lists (one query → results[*][0])
    docs      = results["documents"][0]
    metas     = results["metadatas"][0]
    distances = results["distances"][0]
    ids       = results["ids"][0]

    output: list[dict] = []
    for rank, (doc, meta, dist, chunk_id) in enumerate(
        zip(docs, metas, distances, ids), start=1
    ):
        output.append({
            "id": int(chunk_id),
            "content": doc,
            "metadata": meta,
            "_score": round(dist, 6),       # cosine distance (0 = identical)
            "_rank": rank,
        })

    return output


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Build Chroma vectorstore and run a test query."
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force-rebuild the Chroma collection even if it already exists.",
    )
    parser.add_argument(
        "--query",
        type=str,
        default="What are the three equations of motion?",
        help="Test query to run after building the vectorstore.",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Number of results to retrieve (default: 5).",
    )
    args = parser.parse_args()

    # 1. Build / load the vectorstore
    build_vectorstore(force_rebuild=args.rebuild)

    # 2. Run the test query
    print(f"\n🔍 Query: {args.query!r}  (k={args.k})\n")
    hits = retrieve(args.query, k=args.k)
    for hit in hits:
        meta = hit["metadata"]
        print(
            f"  [{hit['_rank']}] score={hit['_score']:.4f}  "
            f"id={hit['id']}  "
            f"type={meta.get('content_type','?'):<12}  "
            f"topic={meta.get('topic','?')}"
        )
        print(f"      {hit['content'][:120].strip().replace(chr(10),' ')} …\n")
