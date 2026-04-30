"""
Teacher mode module for generating answers with citations and explanations.
"""

def generate_with_citations(question: str, retriever, generate_fn):
    """
    Generate an answer with citations from the retrieved sources.
    
    Args:
        question: User question
        retriever: Retrieval object to get relevant context
        generate_fn: Generation function to create answers
    
    Returns:
        Dictionary with answer and citations
    """
    # Generate the base answer
    result = generate_fn(question, retriever)
    
    # Add citations formatting
    answer = result["answer"]
    retrieved = result.get("retrieved", [])
    retrieved_chunks = result.get("retrieved_chunks", [])
    
    # Build citations
    citations = []
    if retrieved_chunks:
        for i, chunk in enumerate(retrieved_chunks, 1):
            if isinstance(chunk, dict) and "metadata" in chunk:
                source_text = chunk.get("metadata", {})
                source_info = f"Chapter {source_text.get('chapter', 'Unknown')}"
                citations.append(f"[{i}] {source_info}")
            else:
                citations.append(f"[{i}] NCERT Content")
    
    # Format answer with citations
    formatted_answer = f"{answer}"
    if citations:
        formatted_answer += "\n\n**Sources:**\n" + "\n".join(citations)
    
    result["answer"] = formatted_answer
    result["citations"] = citations
    result["teacher_mode"] = True
    
    return result
