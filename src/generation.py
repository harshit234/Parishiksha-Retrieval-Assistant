import os
from dotenv import load_dotenv
from openai import OpenAI
from src import retrieval

load_dotenv()

SYSTEM_PROMPT = """\
You are PariShiksha, an NCERT Class 9 Science tutor.

STRICT RULES — follow every one, no exceptions:

1. **ONLY use the CONTEXT below.** Never use outside knowledge.
2. **Cite your sources** by appending [chunk <id>] after every claim.
   Example: "Force equals mass times acceleration [chunk 11]."
3. **Refuse clearly** when the context cannot answer the question.
   Reply EXACTLY: "Sorry, this is outside the NCERT chapters I have access to."
   Do NOT guess, do NOT paraphrase outside material.
4. **Language**: simple, Class-9-appropriate English. Use bullet points
   and headings where helpful.
5. **No hallucination**: if unsure, refuse rather than fabricate.
"""

USER_PROMPT_TEMPLATE = """\
CONTEXT (retrieved chunks):
{context}

QUESTION:
{question}

Answer (cite each claim with [chunk <id>]):"""


def _get_client() -> OpenAI:
    return OpenAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )


def _build_context(chunks: list[dict]) -> str:
    parts = []
    for chunk in chunks:
        cid = chunk.get("id", "?")
        meta = chunk.get("metadata", {})
        chapter = meta.get("chapter", "")
        page = meta.get("page_start", "")
        header = f"[chunk {cid} | {chapter} p.{page}]"
        parts.append(f"{header}\n{chunk['content']}")
    return "\n\n---\n\n".join(parts)


def ask(question: str, retriever=None, top_k: int = 3) -> dict:
    if retriever is None:
        retriever = retrieval.retriever

    retrieved = retriever.retrieve(question, top_k=top_k)

    chunk_ids = [c.get("id", -1) for c in retrieved]
    sources = [
        f"{c.get('metadata', {}).get('chapter', '?')} p.{c.get('metadata', {}).get('page_start', '?')}"
        for c in retrieved
    ]

    context = _build_context(retrieved)
    user_msg = USER_PROMPT_TEMPLATE.format(context=context, question=question)

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return {
            "answer": f"[No LLM key] Raw context:\n{context[:600]}...",
            "sources": sources,
            "chunk_ids": chunk_ids,
        }

    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0,
        )
        answer = resp.choices[0].message.content.strip()
    except Exception as exc:
        answer = f"[LLM error: {exc}] Falling back to raw context:\n{context[:600]}..."

    return {
        "answer": answer,
        "sources": sources,
        "chunk_ids": chunk_ids,
    }


if __name__ == "__main__":
    result = ask("What is Newton's second law of motion?")
    print("Answer:", result["answer"])
    print("Sources:", result["sources"])
    print("Chunk IDs:", result["chunk_ids"])