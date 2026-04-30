# Reflection Questionnaire – PariShiksha Retrieval-Ready Study Assistant

**Student**: Harshit  
**Date**: April 2026

## Part A — Your implementation artifacts

**A1. Your chunking parameters**  
Final parameters:  
- Chunk size: **512 tokens**  
- Overlap: **128 tokens**  
- Special handling: RecursiveCharacterTextSplitter + regex to preserve worked examples and solutions together. Content-type metadata added.

The key experiment: Started with 256 tokens (no overlap). Many worked-example questions failed because problem and solution got split. After increasing to 512 + 128 overlap, correctness improved from 11/20 to 15/20.

**A2. A retrieved chunk that was wrong for its query**  
**Retrieved Chunk** (for query about Newton’s Second Law):  
> "In the previous chapter we studied uniform motion and acceleration due to gravity..."

**Why it was returned**: High lexical overlap on words like "force", "mass", "acceleration" from Chapter 8 (Motion), even though the correct content was in Chapter 9. This highlighted the need for chapter-level metadata filtering.

**A3. Your grounding prompt, v1 and v(final)**  
**v1**: "Answer using only the provided context."  
**v(final)**: Strict instruction with exact refusal phrase + "Do not use any external knowledge."

Observation: v1 caused synthesis on out-of-scope questions. v(final) improved refusal accuracy significantly.

## Part B — Numbers from your evaluation

**B1. Your evaluation scores** (20 questions)  
- Correct: **15**  
- Grounded: **19**  
- Appropriate refusals: **4/4**

Most concerning was the 15/20 correctness — mostly due to chunk splitting and cross-chapter retrieval noise.

**B2. Chunk-size experiment**  
256 vs 512 tokens → +4 correctness improvement with larger chunks.

**B3. Model family comparison**  
Compared: RoBERTa-SQuAD (extractive), Flan-T5-base, Grok (via xAI API).  
Grok performed best on reasoning questions.

## Part C — Debugging moments

**C1. Most frustrating bug**  
`FileNotFoundError` in chunking because corpus extraction wasn't run first. Took time to debug path issues. Fix: Added proper checks and ran corpus.py before chunking.

**C2. What still bothers you**  
Cross-chapter retrieval noise (Motion content retrieved for Force questions). Will fix with metadata filtering + reranking next week.

## Part D — Architecture and reasoning

**D1. Why not just ChatGPT?**  
ChatGPT often adds external facts or slightly different wording than NCERT. In eval, one question about "retardation" got non-NCERT explanation. Grounded system always sticks to textbook.

**D2. The GANs reflection**  
GANs are for creative generation. Here we need **faithful reproduction** of textbook content. Using GANs would increase hallucinations, which is unacceptable for education.

**D3. Honest pilot readiness**  
Not ready for 100 students yet. Need better metadata filtering, more diverse eval set, and citation support first.

## Part E — Effort and self-assessment

**E1. Effort rating**: 9/10. Proud of implementing smart chunking that preserves examples.

**E2.** Stronger student would have added dense retrieval + reranking already.

**E3.** With two more days: First → Add citations, Last → Full paraphrase robustness test.

---

