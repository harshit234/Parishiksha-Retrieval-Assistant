"""
Guardrails module for safe answer generation with content validation.
"""

def safe_generate(question: str, retriever, generate_fn):
    """
    Generate an answer with safety checks and guardrails.
    
    Args:
        question: User question
        retriever: Retrieval object to get relevant context
        generate_fn: Generation function to create answers
    
    Returns:
        Dictionary with answer and metadata
    """
    # Validate question
    if not question or len(question.strip()) < 3:
        return {
            "answer": "Please ask a more specific question.",
            "retrieved": [],
            "retrieved_chunks": [],
            "safety_flags": ["invalid_question"]
        }
    
    # Generate answer using the provided function
    result = generate_fn(question, retriever)
    
    # Add safety metadata
    result["safety_flags"] = []
    result["safe_mode"] = True
    
    # Check for inappropriate content indicators
    answer_lower = result["answer"].lower()
    unsafe_keywords = ["violence", "harm", "illegal", "dangerous"]
    
    for keyword in unsafe_keywords:
        if keyword in answer_lower:
            result["safety_flags"].append(f"potential_{keyword}")
    
    return result
