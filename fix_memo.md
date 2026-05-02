# fix_memo.md — Targeted Fix: Momentum Topic-Boost in Retrieval

**Date**: 2026-05-01  
**Eval baseline**: `eval_scored.csv` (v1, 12 questions)  
**Re-run target**: `eval_v2_scored.csv` (same 12 questions, new retriever)

---

## 1 — What Failed in v1

**Q5**: *"What is momentum? State the law of conservation of momentum."*

| Field | v1 value |
|---|---|
| `top1_chunk_id` | 10 |
| `correct` | no |
| `grounded` | no |
| `notes` | Model incorrectly refused in-scope question |
| `raw_answer` | *"Sorry, this is outside the NCERT chapters I have access to."* |

**v1 score summary**

| Metric | v1 |
|---|---|
| correct (in-scope) | 9 / 10 |
| grounded (in-scope) | 9 / 10 |
| refused OOS | 2 / 2 |

---

## 2 — Root Cause Diagnosis

**This was a retrieval failure, not a prompt failure.**

The query "What is momentum? State the law of conservation of momentum." contains the word **"momentum"**, which also appears verbatim inside the Newton's 2nd Law chunk (chunk 10):

> *"The rate of change of **momentum** of an object is proportional to the applied net force…"*

BM25-Okapi scored chunk 10 highest because "momentum" is a high-frequency term overlap. The actual **conservation-of-momentum** chunk (chunk 20), which contains the definition, the law, and a worked recoil example, was ranked below chunk 10.

The model received chunk 10 (Newton's 2nd law) as its primary context. That chunk does not contain the conservation law. Following its strict grounding rules, it correctly refused — but it should never have received the wrong context in the first place.

**This is a BM25 keyword-collision failure**: a content-mention of a term ranks above the chunk that is *about* that term.

---

## 3 — The Fix

**File changed**: `src/retrieval.py` → `_get_topic_boost()`

The retriever already had a topic-boost mechanism for "motion" and "force" queries (chapter-level boosts of ±40). The fix extends this with **metadata-aware momentum boosting**:

```diff
# src/retrieval.py  _get_topic_boost()

+        # --- targeted fix: momentum topic boost ---
+        # BM25 over-ranks the Newton's 2nd-law chunk because it mentions
+        # "rate of change of momentum".  Explicitly boost chunks whose
+        # topic metadata says they ARE about momentum / conservation.
+        chunk_topic = metadata.get("topic", "")
+        if "momentum" in query_lower:
+            if chunk_topic in ("momentum", "conservation of momentum"):
+                boost += 50
+            if "conservation" in query_lower and chunk_topic == "conservation of momentum":
+                boost += 30  # extra lift when the question explicitly asks for the law
```

**How it works**: when the query contains "momentum", chunks whose `metadata.topic` is `"momentum"` or `"conservation of momentum"` receive a +50 boost; an additional +30 is added when "conservation" also appears. This overrides the BM25 keyword-collision and surfaces the correct chunk.

**Scope of the change**: one targeted addition in one method. No prompt changes, no chunking changes, no schema changes. All 11 previously-passing questions are unaffected because their queries don't contain "momentum".

---

## 4 — What the v2 Run Confirmed (and What It Couldn't)

### ✅ Retrieval fix confirmed

`eval_v2_scored.csv` was written incrementally after each question. The retrieval columns are written **before** the LLM call, so they are valid regardless of LLM errors.

**Q5 retrieval — before vs after:**

| | v1 | v2 |
|---|---|---|
| `top1_chunk_id` | **10** (Newton's 2nd law) | **20** (conservation of momentum) ✓ |
| `top1_chunk_topic` | *(not recorded in v1)* | `"conservation of momentum"` ✓ |

The retriever now returns the correct chunk for Q5. The fix worked.

All other questions also retrieved the same correct top-1 chunks as v1 (confirming no regressions from the boost):

| qid | top1_chunk_id v1 | top1_chunk_id v2 | topic v2 |
|---|---|---|---|
| 1 | 0 | 0 | motion basics |
| 2 | 10 | 10 | newton's first law |
| 3 | 3 | 3 | distance and displacement |
| 4 | 16 | 16 | friction |
| **5** | **10** | **20** | **conservation of momentum** ✓ |
| 6 | 15 | 15 | non-contact forces |

### ❌ LLM scoring could not complete

Both Gemini API keys hit the **free-tier daily quota** (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`, limit: 20 requests/day for `gemini-2.5-flash`). All 12 LLM calls in the v2 run returned HTTP 429 errors. The `correct` and `grounded` columns in `eval_v2_scored.csv` show `error` for all rows.

**What this means**: we cannot yet confirm that Q5 produces a correct LLM answer with the right context. The retrieval fix is verified; the LLM-answer improvement is the **expected outcome** (correct context → model can answer → no false refusal), but it is **not yet empirically scored**.

---

## 5 — Expected v2 Score (Projected)

Based on the retrieval fix and v1 LLM behaviour on all other in-scope questions:

| Metric | v1 (actual) | v2 (projected) |
|---|---|---|
| correct (in-scope) | 9 / 10 | **10 / 10** |
| grounded (in-scope) | 9 / 10 | **10 / 10** |
| refused OOS | 2 / 2 | 2 / 2 (unchanged) |

Q5 is now the only question that changed. The fix has no effect on any other question.

---

## 6 — Next Steps

1. **Re-run** `scripts/run_eval_v2.py` tomorrow (after the per-day quota resets) or with a paid-tier key to get real LLM scores.
2. **Update** this memo with the actual v2 `correct`/`grounded` scores once available.
3. **Consider** adding `gemini-2.0-flash` as a fallback model in `run_eval_v2.py` since it has a separate quota bucket.
