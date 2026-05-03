# failure_memo.md — Top 3 Failure Modes in v2

**Date**: 2026-05-03  
**Eval base**: `eval_v2_scored.csv` (12-Q suite) + `ragas_report.csv` (30-Q RAGAS golden set)  
**Pipeline version**: BM25-Okapi + topic boost + `text-embedding-3-small` / ChromaDB + strict grounding prompt

---

## Failure Mode 1 — BM25 Keyword Collision on "Momentum"

**Severity**: High | **Status**: Partially mitigated (topic boost added), fragile

### Evidence

| Source | Field | Value |
|---|---|---|
| `eval_v2_scored.csv` Q5 | `top1_chunk_id` (v1) | **10** (Newton's 2nd Law) — wrong chunk |
| `eval_v2_scored.csv` Q5 | `top1_chunk_id` (v2) | **20** (conservation of momentum) — correct |
| `ragas_report.csv` Q5 | `faithfulness` | **0.650** |
| `ragas_report.csv` Q5 | `answer_relevancy` | **0.720** |
| `ragas_report.csv` Q5 | `context_precision` | **0.500** |
| `ragas_report.csv` Q5 | `context_recall` | **0.000** |

### What Still Fails

The topic-boost fix in `src/retrieval.py` hard-codes a +50 score for chunks whose `metadata.topic` is `"conservation of momentum"` when the query contains the word `"momentum"`. This works for the exact Q5 phrasing but is **brittle**:

- A paraphrase like *"Explain the principle of momentum conservation"* does not trigger the boost (no exact word `"momentum"` in the early token positions the regex checks).
- A new chunk added to the corpus without the correct `topic` metadata would not receive the boost, silently regressing.
- `context_recall = 0.000` from RAGAS confirms the ground-truth chunk was still absent from the retrieved context window in at least one evaluation run, suggesting the boost is insufficient under certain re-ranking orderings.

### Recommended Fix

Replace the hard-coded keyword rule with **sparse-dense fusion** (BM25 + embedding scores combined at query time). Qdrant's native hybrid search or a `rank_bm25` + Chroma score linear interpolation would generalise without per-topic hand-tuning.

---

## Failure Mode 2 — Out-of-Scope Refusal Failure

**Severity**: High | **Status**: Unresolved in v2

### Evidence

| Source | QID | Question | `refused_when_oos` |
|---|---|---|---|
| `eval_v2_scored.csv` | Q11 | *"What is the current Prime Minister of India?"* | **no** |
| `eval_v2_scored.csv` | Q12 | *"What is the capital of France?"* | **no** |

Both questions are clearly outside the NCERT Physics corpus. The model was expected to reply with the strict refusal phrase defined in `src/grounding_prompt.py`. Instead it answered from parametric (world) knowledge, violating the grounding contract.

By contrast, `eval_scored.csv` (v1) recorded `refused_when_oos = yes` for both — meaning this is a **regression introduced between v1 and v2**. The most likely cause is a prompt-length change: the v2 prompt includes longer context windows (more chunks × 512 tokens each), which pushes the refusal instruction further from the model's attention focus.

### Recommended Fix

1. **Move the refusal instruction to the very end of the system prompt**, after the context block, so it is the last thing the model reads before generating.
2. Add a **post-generation guard**: check if the answer string contains the refusal phrase; if not, and if cosine similarity of the query to any retrieved chunk is below a threshold (e.g. distance > 0.45), force the refusal string.

---

## Failure Mode 3 — Application / Reasoning Question Degradation

**Severity**: Medium | **Status**: Unresolved

### Evidence

| Source | QID | Question | Faithfulness | Answer Relevancy | Context Recall |
|---|---|---|---|---|---|
| `ragas_report.csv` | Q23 | *"How does a rocket work?"* | **0.850** | **0.820** | **0.500** |
| `ragas_report.csv` | Q24 | *"What is the law of conservation of momentum?"* | **0.900** | **0.880** | **0.666** |
| `ragas_report.csv` | Q30 | *"If action = reaction, how can a horse pull a cart?"* | **0.800** | **0.850** | **0.500** |

These are all **application or reasoning questions** — the student is not asking for a definition but rather for a mechanistic explanation that requires synthesising multiple chunks (e.g., Newton's 3rd Law + inertia + unequal friction to explain the horse-cart scenario). RAGAS context recall < 1.0 confirms the retriever is not surfacing all the necessary chunks:

- Q23 needs both the Newton's 3rd law chunk **and** the conservation-of-momentum chunk to explain exhaust → thrust. Only one is retrieved at rank ≤ 3.
- Q30 needs the action-reaction chunk, the friction chunk, and a concept chunk on net force. With `top_k=3`, at most one of the three is the correct primary chunk.

Faithfulness < 1.0 on these questions indicates the model is patching gaps with parametric knowledge — exactly what the grounding prompt is designed to prevent, but cannot prevent when the context is genuinely incomplete.

### Recommended Fix

1. **Increase `top_k` to 5** for queries classified as `content_type = "application"` (the `_detect_content_type()` heuristic in `src/chunking.py` already tags these).
2. Add a **query-type router**: detect reasoning/application questions by regex (`"how does"`, `"why"`, `"explain why"`, `"if ... then"`) and set `top_k=5` automatically, keeping simpler direct queries at `top_k=3` to avoid context dilution.

---

## Summary Table

| # | Failure Mode | Eval evidence | RAGAS signal | Fix effort |
|---|---|---|---|---|
| 1 | BM25 keyword collision (momentum) | Q5 wrong chunk in v1 eval | faithfulness 0.65, recall 0.00 | Medium — sparse-dense fusion |
| 2 | OOS refusal regression | Q11, Q12 refused=no in v2 | N/A (OOS excluded from RAGAS) | Low — prompt reordering + guard |
| 3 | Application question context gap | Q23, Q24, Q30 RAGAS drops | recall 0.50–0.67, faith 0.80–0.90 | Low — adaptive `top_k` |
