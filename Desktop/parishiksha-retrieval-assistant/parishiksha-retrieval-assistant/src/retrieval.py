# src/retrieval.py (Enhanced Version with Better Pattern Matching)
from rank_bm25 import BM25Okapi
import json
import re

with open("data/processed/chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

class Retriever:
    def __init__(self):
        self.chunks = chunks
        self.corpus = [chunk["content"].lower().split() for chunk in chunks]
        self.bm25 = BM25Okapi(self.corpus)

    def _get_topic_boost(self, query: str, chunk: dict) -> int:
        query_lower = query.lower()
        content_lower = chunk["content"].lower()
        metadata = chunk.get("metadata", {})
        chapter = metadata.get("chapter", "").lower()
        
        boost = 0
        
        # Strong topic matching
        if "motion" in query_lower and "motion" in chapter:
            boost += 40
        if "force" in query_lower and ("force" in chapter or "newton" in chapter):
            boost += 40
            
        # Content keyword boost
        if "motion" in query_lower and "motion" in content_lower:
            boost += 15
        if "force" in query_lower and "force" in content_lower:
            boost += 15
            
        return boost

    def retrieve(self, query: str, top_k=3):
        query_lower = query.lower()
        scores = self.bm25.get_scores(query_lower.split())
        
        reranked = []
        for idx, score in enumerate(scores):
            chunk = self.chunks[idx]
            final_score = score
            
            # Apply topic boost
            final_score += self._get_topic_boost(query, chunk)
            
            # Penalty for wrong chapter
            if "motion" in query_lower and "force" in chunk.get("metadata", {}).get("chapter", "").lower():
                final_score -= 35
            if "force" in query_lower and "motion" in chunk.get("metadata", {}).get("chapter", "").lower():
                final_score -= 35
            
            reranked.append((idx, final_score))
        
        # Sort and get top results
        sorted_chunks = sorted(reranked, key=lambda x: x[1], reverse=True)
        top_indices = [idx for idx, _ in sorted_chunks[:top_k]]
        
        return [self.chunks[i] for i in top_indices]


# Initialize retriever
retriever = Retriever()