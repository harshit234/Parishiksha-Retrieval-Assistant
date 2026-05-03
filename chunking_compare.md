# chunking_compare.md — Chunking Strategy Micro-Eval

**Project**: PariShiksha Retrieval-Ready Study Assistant  
**Task**: Compare two chunking strategies on the core 10-question in-scope evaluation set.  
**Corpus**: NCERT Physics (Chapter 8: Motion, Chapter 9: Force)

---

## 1 — The Variants

| Parameter | Variant A (Baseline) | Variant B (Upgraded) |
|---|---|---|
| **Chunk Size** | 256 tokens | **512 tokens** |
| **Overlap** | 0 tokens | **128 tokens** |
| **Splitter** | Character splitting (naïve) | `RecursiveCharacterTextSplitter` |
| **Metadata** | Flat (chapter, topic) | Rich (`token_count`, `content_type`, `page_start`) |
| **Total Chunks** | ~35 small chunks | 24 semantic chunks |

---

## 2 — 10-Q Micro-Eval Results

This evaluation focuses strictly on the 10 **in-scope** questions from the primary eval suite. (Out-of-scope questions evaluate the grounding prompt, not the chunking strategy).

| QID | Question Focus | Variant A Correctness | Variant B Correctness | Root cause of Variant A failure |
|---|---|:---:|:---:|---|
| Q1 | What is motion? | ✅ | ✅ | (Easy definition, fits in small chunk) |
| Q2 | Newton's second law | ✅ | ✅ | (Standard definition) |
| Q3 | Distance vs displacement | ❌ | ✅ | Comparison split across chunks without overlap |
| Q4 | Friction and types | ✅ | ✅ | |
| Q5 | Momentum & conservation | ❌ | ❌* | Retrieval collision (fixed later via topic boost) |
| Q6 | Non-contact forces | ✅ | ✅ | |
| Q7 | Weight vs mass | ❌ | ✅ | Concepts split; "mass" context lost |
| Q8 | Uniform circular motion | ✅ | ✅ | |
| Q9 | Calculate recoil velocity (5kg gun) | ❌ | ✅ | **Problem statement and solution split** |
| Q10 | Push against wall (paraphrase) | ✅ | ✅ | |

*\*Q5 failed in Variant B due to a BM25 keyword collision, not a chunking boundary issue. This was addressed in a separate retrieval fix.*

### Score Summary

* **Variant A (256/0)**: 6 / 10 Correct
* **Variant B (512/128)**: 9 / 10 Correct

---

## 3 — Key Failure Modes Addressed by Variant B

### Failure Mode 1: The "Worked-Example Split" (Q9)
**Impacted Question**: Calculate the recoil velocity of a 5 kg gun...
* **Why Variant A failed**: At 256 tokens with zero overlap, NCERT physics examples were frequently severed halfway. The chunking boundary would often fall right between the *Given* values and the *Calculation* steps. The retriever would fetch the calculation chunk, but without the setup parameters, the LLM hallucinated the missing numbers.
* **Why Variant B succeeded**: 512 tokens easily encompasses an entire worked example. The 128-token overlap ensures that even if a split happens near an example, the context bleeds over enough for the LLM to reconstruct the logic.

### Failure Mode 2: Multi-Concept Fragmentation (Q3, Q7)
**Impacted Questions**: Distance vs Displacement; Weight vs Mass
* **Why Variant A failed**: Textbooks often introduce concept A, spend a paragraph explaining it, and then introduce concept B as a contrast. At 256 tokens, Concept A and Concept B ended up in separate chunks. If the query asked for the *difference* between them, the retriever struggled to surface both chunks simultaneously within the `top_k=3` limit.
* **Why Variant B succeeded**: The larger 512-token window naturally encapsulates broader semantic units. "Weight vs Mass" fits neatly into a single chunk, allowing a single vector retrieval to supply both sides of the comparison to the LLM.

---

## 4 — Conclusion & Recommendation

The naïve 256-token strategy suffers from high fragmentation, severely hurting performance on comparative questions and numerical examples. 

**Recommendation**: The `RecursiveCharacterTextSplitter` configured to **512 tokens with 128 overlap** (Variant B) is vastly superior for textbook content. It preserves semantic units (worked examples, paired concepts) while remaining well within the context window limits of standard LLMs, directly lifting in-scope correctness from 60% to 90%.
