import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize Grok client
client = OpenAI(
    api_key=os.getenv("xai-ohvSSP8qD4amrieVrrbO3cmIxQVTAlNqzsNI6Q7JSFluEACjWo02Xy0vqwZscpDgcudT24Svl9Ju4AI3"),
    base_url="https://api.x.ai/v1"
)

# ==================== NATURAL & HUMAN-LIKE PROMPT ====================
GROUNDING_PROMPT = """
You are PariShiksha, a friendly and patient NCERT Class 9 Science teacher.

Answer the student's question in simple, clear language that a 14-year-old can easily understand.
Use short sentences and bullet points when it helps clarity.
Never mention "context", "chunk", or "retrieved".
If the answer is not available in the given NCERT content, politely say:
"I'm sorry, this information is not covered in the chapters I have access to."

Context:
{context}

Question: {question}

Answer:
"""

def generate_answer(question: str, retriever=None):
    # Use provided retriever or default
    if retriever is None:
        from src.retrieval import retriever as default_retriever
        retriever = default_retriever

    # Retrieve relevant chunks
    retrieved = retriever.retrieve(question, top_k=3)
    context = "\n\n---\n\n".join([chunk["content"] for chunk in retrieved])

    # Build prompt
    prompt = GROUNDING_PROMPT.format(context=context, question=question)

    try:
        response = client.chat.completions.create(
            model="grok-4-1-fast-reasoning",   # or "grok-beta" if you prefer
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=700
        )
        
        answer = response.choices[0].message.content.strip()
        
        return {
            "answer": answer,
            "retrieved_chunks": retrieved
        }

    except Exception as e:
        # Graceful fallback (never show raw context to user)
        return {
            "answer": "I'm sorry, I'm having trouble connecting right now. Please try asking your question again.",
            "retrieved_chunks": retrieved
        }