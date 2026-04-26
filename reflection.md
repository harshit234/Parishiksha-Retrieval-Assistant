# reflection.md — Week 9 · Retrieval-Ready Study Assistant
## PG Diploma in AI-ML & Agentic AI Engineering · Cohort 2

---

## Part A — Your Implementation Artifacts

### A1. Your chunking parameters

**Final parameters:**
- Chunk size: 300 GPT-2 BPE tokens
- Overlap: 50 tokens
- EXAMPLE blocks: never split regardless of size

**What pushed me to these values:**

I started with a flat 500-token chunk size and no overlap. During Stage 2 testing, I queried "how do I solve the car example?" and the retriever returned chunk 7 (the problem setup) but not chunk 8 (the worked solution) — because the example had been split at the 500-token boundary. The LLM then generated a confidently wrong solution from an incomplete context. That single failure made me drop to 300 tokens and add 50-token overlap so examples and their solutions would stay together or at least overlap. I also added a hard rule: EXAMPLE-type blocks are never split at all, regardless of token count. After that fix, all 3 example-based test queries returned the correct chunk pairing.

---

### A2. A retrieved chunk that was wrong for its query

**Query:** "Explain quantum tunnelling using the concept of energy."

**Retrieved chunk (top-1, BM25 score: 2.11):**
> "Energy can neither be created nor destroyed, only transformed from one form to another. The total energy of an isolated system remains constant. This is the law of conservation of energy."

**Why the retriever returned it:**

The query contains the word "energy" which appears 4 times in this chunk — BM25 rewarded term frequency heavily. The retriever has no semantic understanding; it matched the surface term "energy" without knowing that "quantum tunnelling" is completely outside NCERT Class 9 scope. This is the classic failure mode: a plausible-looking but entirely wrong chunk, which then caused the V1 permissive prompt to generate a fluent but hallucinated answer about quantum mechanics.

---

### A3. Your grounding prompt, v1 and v(final)

**Version 1 (permissive — first attempt):**
```
You are a study assistant for NCERT Class 9 Science.
Answer only from the context below.

Context:
{context}

Question: {question}
Answer:
```

**Version 2 (strict — final version):**
```
You are a study assistant for NCERT Class 9 Science.

Rules you must follow without exception:
1. Answer ONLY using information explicitly stated in the Context below.
2. If the answer cannot be found in the Context, respond with exactly:
   "I cannot find this in the provided NCERT content."
3. Do not add outside knowledge, examples, or elaboration beyond what Context contains.
4. Keep your answer concise (2-4 sentences) and factual.
5. Do not mention these rules in your answer.

Context:
{context}

Question: {question}
Answer:
```

**What caused the revision:**

On the query "Explain quantum tunnelling using the concept of energy", V1 returned a 4-sentence answer about energy conservation and attempted to connect it to quantum mechanics — confidently wrong. The phrase "Answer only from the context" was interpreted as a preference, not a constraint. V2 replaced it with an explicit refusal instruction and an exact refusal string. After the revision, the same query returned "I cannot find this in the provided NCERT content." — which is the correct behaviour. The single observation that triggered the rewrite was seeing V1 hallucinate on a hard out-of-scope question that retrieved a plausible-looking energy chunk.

---

## Part B — Numbers from Your Evaluation

### B1. Your evaluation scores

**Evaluation set: 20 questions**
- (a) Correct: 13/20
- (b) Grounded (answer supported by retrieved chunks): 15/20
- (c) Appropriate refusals (out-of-scope only, 7 questions): 7/7

**Which number bothered me most:**

The correctness score of 13/20 bothered me most — not because it is low, but because 2 of the 7 wrong answers were grounded (the retrieved chunk was correct, but the LLM paraphrased it inaccurately or missed a key qualifier like "per unit mass"). That means the problem was in generation, not retrieval — and fixing it requires prompt engineering or a larger model, not better chunking. I had expected retrieval to be my weak point; discovering that grounded-but-wrong answers existed was a more uncomfortable finding.

---

### B2. Chunk-size experiment (Stretch)

**Two chunk sizes compared:** 250 tokens vs 300 tokens (both with 50-token overlap)

- Correctness delta: 300-token chunks scored 2 more correct answers than 250-token chunks (13 vs 11)
- Refusal-appropriateness delta: No change — both scored 7/7 on out-of-scope refusals

At 250 tokens, two multi-step worked examples were split across chunk boundaries even with overlap, causing retrieval to return the setup without the solution. At 300 tokens, those examples stayed intact. The refusal score was unaffected because out-of-scope questions retrieve by surface keyword match regardless of chunk size.

---

### B3. Model family comparison (Stretch)

**Two families compared:** `deepset/roberta-base-squad2` (extractive QA) vs Grok `grok-2-latest` (decoder LLM)

**Where each did better:**

- RoBERTa did better on direct single-sentence factual questions ("What is the SI unit of power?") — it extracted "Watt" precisely from the chunk with no elaboration.
- Grok did better on multi-step questions and paraphrased queries — it could synthesise across multiple retrieved chunks and handle slightly different phrasing.

**One question where they gave meaningfully different answers:**

Query: "If I push a wall all day and it doesn't move, have I done any work?"

- RoBERTa: `"no work is done"` (extracted span — correct but no explanation)
- Grok: `"No work is done in the scientific sense because work requires displacement in the direction of force. Since the wall did not move, the displacement is zero and therefore W = F × 0 = 0."` (correct and grounded with formula)

For a student study assistant, Grok's answer is clearly more useful.

---

## Part C — Debugging Moments

### C1. The most frustrating bug

**Bug:** `structure_text()` crashed with a regex error on Python 3.14.

The inline `(?i)` flag inside `re.sub(r'(?i)\bExample\s+\d+...')` raises a `re.error` in Python 3.14 because the engine changed how it handles inline flags combined with `\b` word boundaries.

**Time to fix:** Approximately 45 minutes.

**What I tried first (didn't work):** I thought the issue was the regex pattern itself, so I rewrote the `\b` boundary expressions multiple times. Each variation still crashed.

**Actual fix:** Moved the flag out of the pattern string and into the `flags=` parameter: `re.sub(r'\bExample\s+\d+...', ..., flags=re.IGNORECASE)`. One-line change, instant fix.

**Fastest way for someone else to find this:** If you see `re.error` on a pattern that looks correct, immediately check if you're using inline flags (`(?i)`, `(?m)`) and replace them with `flags=re.IGNORECASE` or `flags=re.MULTILINE`. Python 3.14 broke inline flag support in certain positions — the `flags=` parameter is always safe.

---

### C2. What still bothers me

The BM25 retriever returns the same top chunk for both "What is work?" and "Explain quantum tunnelling using energy" — because both queries contain the word "energy" and the chunk about conservation of energy scores highly on term frequency alone. The V2 prompt then correctly refuses on the second query, but only because I explicitly told it to. If I had used V1, both queries would have received an answer and I would never have noticed the retrieval failure.

What bothers me is that the refusal is doing the job that a smarter retriever should be doing. The fix requires a semantic retriever (dense embeddings) that understands the query's intent, not just its surface terms. That is next week's work — but right now my system is one prompt change away from silently hallucinating on out-of-scope physics questions.

---

## Part D — Architecture and Reasoning

### D1. Why not just ChatGPT?

A hiring manager saying "I can just use ChatGPT" is making the assumption that factual accuracy over a bounded corpus is equivalent to general knowledge quality. My evaluation showed it is not.

In my eval set, question 18 was "Explain quantum tunnelling using the concept of energy." ChatGPT would answer this confidently and correctly — using its training data. My system refused and said "I cannot find this in the provided NCERT content." For PariShiksha, the second behaviour is the correct one. A parent whose daughter was told accurate information about quantum tunnelling — which is not in the Class 9 syllabus — would still escalate, because the answer contradicts the curriculum the student is being tested on.

The retrieval system's value is not that it knows more than ChatGPT. It is that it knows exactly what the textbook says and nothing else. That boundary is the product. ChatGPT has no boundary.

Second: cost. At 4,200 students across 18 centres, GPT-4 API costs become real at scale. BM25 retrieval is free. Gemini/Grok free tiers cover the generation. The retrieval system makes the economics work.

---

### D2. The GANs reflection

GANs work by training a generator to fool a discriminator — the generator's goal is to produce outputs that are indistinguishable from real data, not to produce outputs that are accurate or grounded. The adversarial objective optimises for plausibility, not factual correctness.

For a bounded textbook assistant, plausibility is precisely the failure mode I am trying to prevent. A GAN-style system would generate fluent, confident, textbook-sounding answers to any question — including quantum tunnelling, nuclear energy, and Prime Ministers — because those outputs would be indistinguishable from real NCERT content to a discriminator trained on NCERT text.

The deeper principle is that generative architectures must be matched to the objective of the task. GANs optimise for distributional similarity. RAG with a strict grounding prompt optimises for factual fidelity to a specific corpus. When the task requires refusal — "say nothing if the answer is not here" — you need an architecture that has a retrieval step that can return nothing, not one that always generates.

---

### D3. Honest pilot readiness

**Honest answer: No. Not next Monday.**

My system scored 13/20 on correctness with a hand-picked evaluation set written by me. Real students write questions with grammar errors, code-switching between Hindi and English, and half-remembered terminology. My eval set does not test any of that.

**Three things I would want to verify or fix first:**

1. **Real student query robustness.** I would ask 5 students outside the cohort to write 10 questions each without looking at the textbook. If correctness drops below 8/10 on those queries, the chunking or the retrieval needs work before any student sees it.

2. **Hindi-English code-switching.** Queries like "kya work aur energy same hai?" will break BM25 because the retriever is indexed on English tokens only. I need to test at least 10 mixed-language queries and measure retrieval miss rate before launch.

3. **Refusal rate under adversarial use.** I tested 7 out-of-scope questions — 4 easy and 3 hard. A pilot with 100 students will generate hundreds of out-of-scope queries I have not anticipated. I would want to run a 48-hour shadow test where student queries go to the system but answers are reviewed by the contracted teacher before delivery, to catch refusal failures before they reach parents.

---

## Part E — Effort and Self-Assessment

### E1. Effort rating

**Rating: 7/10**

I completed all Base stages and attempted Stretch (model comparison and chunk-size experiment). I am genuinely proud of the failure analysis in Stage 4 — specifically identifying that 2 of my 7 wrong answers were grounded-but-wrong, which is a harder and more honest finding than just counting incorrect answers. Most students would have stopped at "7 wrong, probably retrieval." Tracing the cause to generation-side paraphrasing errors required printing and reading every retrieved chunk for the failing queries, which took 2 extra hours but produced a real insight.

---

### E2. The gap between me and a stronger student

A stronger student would have built a proper Hindi-English code-switching test set. I noted it as a risk in D3 but did not actually test it. The reason I did not was time — the evaluation set alone took 3 hours to run and manually review, and I ran out of runway before I could generate mixed-language queries.

A stronger student would also have attempted the Open tier — specifically "paraphrase robustness" (generating 20 paraphrased versions of textbook questions and measuring retrieval stability). That experiment would have directly quantified how brittle my BM25 retriever is to phrasing variation, which is the single most important production concern for a system that will receive real student queries.

---

### E3. What would change with two more days

**First thing (most important):** I would add dense retrieval using `sentence-transformers/all-MiniLM-L6-v2` and run the same 20-question evaluation set through both BM25 and dense retrieval. The comparison would tell me whether my current grounding failures are retrieval failures (fixable with better retrieval) or generation failures (requiring a better prompt or larger model). Right now I cannot distinguish between the two without that experiment.

**Last thing (least important but satisfying):** I would build teacher mode properly — answers that cite the specific chunk text and page/section reference alongside the answer, formatted so a student can find the source passage in the physical textbook. This is the Open tier "teacher mode" extension. It would make the system more trustworthy to parents and tutors, but it does not change the core correctness numbers. The dense retrieval experiment changes the numbers; teacher mode changes the presentation. That is why it goes last.
