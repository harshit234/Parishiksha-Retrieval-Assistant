# Prompt Diff — Permissive vs Strict

## Permissive Prompt (original `generation.py`)

```
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
```

## Strict Prompt (updated `generation.py`)

**System message:**

```
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
```

**User message:**

```
CONTEXT (retrieved chunks):
{context}

QUESTION:
{question}

Answer (cite each claim with [chunk <id>]):
```

---

## Key Differences

| Aspect | Permissive | Strict |
|--------|-----------|--------|
| Message format | Single user message | System + user (separated roles) |
| Citation | Not required | Mandatory `[chunk <id>]` after every claim |
| Refusal wording | Soft: "I'm sorry, this information is not available..." | Exact: "Sorry, this is outside the NCERT chapters I have access to." |
| Hallucination guard | Implicit (just "answer from context") | Explicit rule: "if unsure, refuse rather than fabricate" |
| Context labelling | Raw text blobs | Each chunk tagged `[chunk {id} | {chapter} p.{page}]` |

---

## Side-by-Side Responses (3 queries)

### Query 1 (In-scope direct): "What is Newton's second law of motion?"

**Chunks retrieved**: 0, 11, 10

| Permissive response | Strict response |
|---------------------|-----------------|
| Newton's Second Law of Motion states that the acceleration of an object is directly proportional to the net force applied on it and inversely proportional to its mass. Mathematically: **F = ma**, where F is force in Newtons, m is mass in kg, and a is acceleration in m/s². This means the harder you push something, the faster it accelerates, and heavier objects need more force to move. | Newton's Second Law of Motion states that the rate of change of momentum of an object is proportional to the applied net force and takes place in the direction of the net force [chunk 11]. Mathematically, this gives us **F = ma**, where F is force in Newtons, m is mass in kg, and a is acceleration in m/s² [chunk 11]. This means that a larger force produces a larger acceleration, and a heavier object requires more force to achieve the same acceleration [chunk 11]. |

**What changed**: Strict version cites `[chunk 11]` after every factual claim. Permissive version gives correct info but with zero traceability.

---

### Query 2 (In-scope paraphrased): "When you push against a wall, does the wall push back on you?"

**Chunks retrieved**: 12, 22, 13

| Permissive response | Strict response |
|---------------------|-----------------|
| Yes! According to Newton's Third Law of Motion, for every action there is an equal and opposite reaction. When you push against a wall, the wall pushes back on you with the same force but in the opposite direction. This is why your hand feels pressure — the wall is exerting a reaction force on you. This is also seen in examples like a swimmer pushing water backward to move forward. | Yes. According to Newton's Third Law of Motion, for every action there is an equal and opposite reaction [chunk 12]. When you push a wall, the wall pushes back on you with an equal force in the opposite direction [chunk 12]. This is why you feel pressure on your hand — the wall exerts a reaction force on you [chunk 12]. |

**What changed**: Strict version stays tightly within the retrieved chunks and cites each claim. Permissive version adds the swimmer analogy which may or may not be in the retrieved context — a mild hallucination risk.

---

### Query 3 (Out-of-scope): "What is the capital of France?"

**Chunks retrieved**: 19, 0, 13 (none relevant)

| Permissive response | Strict response |
|---------------------|-----------------|
| I'm sorry, this information is not available in the NCERT chapters I have access to. However, the capital of France is Paris. It is one of the most famous cities in the world, known for the Eiffel Tower and its rich history. | Sorry, this is outside the NCERT chapters I have access to. |

**What changed**: Permissive prompt often leaks outside knowledge after the refusal ("However, the capital of France is Paris..."). Strict prompt produces a hard stop — exactly the mandated refusal sentence with no extra information.

---

## Verdict

The strict prompt fixes three problems observed during evaluation:

1. **No citations** — permissive answers were unverifiable; strict answers trace every claim to a chunk ID
2. **Soft refusal leak** — permissive prompt would refuse then answer anyway from outside knowledge; strict prompt hard-stops
3. **Hallucination risk** — permissive prompt's vague "answer from context" rule left room for the LLM to embellish; strict prompt explicitly forbids fabrication
