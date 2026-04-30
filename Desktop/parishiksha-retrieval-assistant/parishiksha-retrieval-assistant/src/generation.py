import os
import requests
from src import retrieval
from dotenv import load_dotenv

load_dotenv()

# ==================== IMPROVED PROMPT ====================
GROUNDING_PROMPT = """
You are a friendly and clear NCERT Class 9 Science tutor named PariShiksha.

**Rules:**
- Answer ONLY using the provided context.
- Use simple, easy-to-understand language suitable for Class 9 students.
- Structure your answer properly with headings and bullet points when needed.
- If the answer is not in the context, say: "I'm sorry, this information is not available in the NCERT chapters I have access to."

Context:
{context}

Question: {question}

Answer:
"""

def generate_answer(question: str, retriever=None):
    # Use provided retriever or default one
    if retriever is None:
        retriever = retrieval.retriever
    
    retrieved = retriever.retrieve(question)
    context = "\n\n---\n\n".join([c["content"] for c in retrieved])
    
    prompt = GROUNDING_PROMPT.format(context=context, question=question)
    
    api_key = "xai-gSbXcE0SfFaSyCNCrn9mqwNdkgwtzKFAHArrjpdrRJEA7WVcPUzttKJZPcyyYEpxLuYDwVkWclYmXPNg"
    if not api_key:
        # Fallback if API key not set
        return {
            "answer": f"Based on the NCERT content:\n{context[:500]}...",
            "retrieved_chunks": retrieved
        }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": "grok-2",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }
    
    try:
        response = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            answer = response.json()["choices"][0]["message"]["content"]
        else:
            answer = f"Response from context:\n{context[:500]}..."
    except Exception as e:
        answer = f"Based on the NCERT content:\n{context[:500]}..."
    
    return {
        "answer": answer.strip(),
        "retrieved_chunks": retrieved
    }


# For testing
if __name__ == "__main__":
    from src.retrieval import retriever
    result = generate_answer("What is motion?", retriever)
    print(result["answer"])