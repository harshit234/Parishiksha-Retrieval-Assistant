from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import json
import re

# Load chunks
with open("data/processed/chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

# Load dense retriever model
dense_model = SentenceTransformer('all-MiniLM-L6-v2')

class Retriever:
    def __init__(self):
        self.chunks = chunks
        self.corpus = [chunk["content"].lower().split() for chunk in self.chunks]
        self.bm25 = BM25Okapi(self.corpus)
        self.dense_model = dense_model
        
        # Pre-compute embeddings for all chunks (as numpy arrays for sklearn)
        self.embeddings = self.dense_model.encode(
            [chunk["content"] for chunk in self.chunks],
            convert_to_tensor=False
        )

    def _get_expected_chapter(self, query: str):
        """Infer which chapter(s) the query is asking about."""
        query_lower = query.lower()
        
        # Motion (Chapter 8) keywords
        motion_keywords = ["motion", "velocity", "acceleration", "speed", "distance", "displacement"]
        # Force (Chapter 9) keywords
        force_keywords = ["force", "newton", "momentum", "friction", "pressure", "mass"]
        
        motion_score = sum(1 for kw in motion_keywords if kw in query_lower)
        force_score = sum(1 for kw in force_keywords if kw in query_lower)
        
        if motion_score > force_score:
            return ["motion", "chapter 8"]
        elif force_score > motion_score:
            return ["force", "chapter 9"]
        else:
            return ["motion", "force", "chapter 8", "chapter 9"]  # Both or unclear

    def retrieve(self, query: str, top_k: int = 2):
        """
        Retrieve most relevant chunks with metadata filtering.
        Uses BM25 + dense retrieval + chapter filtering to avoid cross-chapter noise.
        """
        query_lower = query.lower()
        expected_chapters = self._get_expected_chapter(query)
        
        # Step 1: Get BM25 scores (primary ranking)
        scores = self.bm25.get_scores(query_lower.split())
        
        # Step 2: Get dense retrieval scores
        query_embedding = self.dense_model.encode(query)
        from sklearn.metrics.pairwise import cosine_similarity
        dense_scores = cosine_similarity([query_embedding], self.embeddings)[0]
        
        # Step 3: Combine scores with metadata filtering
        reranked = []
        for idx, bm25_score in enumerate(scores):
            chunk = self.chunks[idx]
            metadata = chunk.get("metadata", {})
            chapter = metadata.get("chapter", "").lower()
            chunk_type = metadata.get("type", "").lower()
            content = chunk["content"].lower()
            topic = metadata.get("topic", "").lower()
            
            # Check if chunk is from expected chapter
            chapter_match = any(ch in chapter for ch in expected_chapters)
            
            # Combine scoring methods
            combined_score = (bm25_score * 0.5) + (dense_scores[idx] * 0.5)
            
            # Apply chapter filtering boost (prefer matching chapters)
            if chapter_match:
                combined_score *= 1.3  # Boost matching chapters
            else:
                combined_score *= 0.7  # Penalize non-matching chapters
            
            # Topic-specific boosts
            if "newton" in query_lower and "newton" in topic:
                combined_score += 0.15
            if "friction" in query_lower and "friction" in topic:
                combined_score += 0.15
            if "momentum" in query_lower and "momentum" in topic:
                combined_score += 0.15
            if "equation" in query_lower and "equation" in chunk_type:
                combined_score += 0.10
            if "law" in query_lower and "law" in topic:
                combined_score += 0.10
            
            reranked.append((idx, combined_score))
        
        # Step 4: Sort and return top_k
        sorted_chunks = sorted(reranked, key=lambda x: x[1], reverse=True)
        top_indices = [idx for idx, _ in sorted_chunks[:top_k]]
        
        return [self.chunks[i] for i in top_indices]


# Initialize global retriever
retriever = Retriever()

print("[OK] Enhanced Retriever with dense embedding + metadata filtering initialized")