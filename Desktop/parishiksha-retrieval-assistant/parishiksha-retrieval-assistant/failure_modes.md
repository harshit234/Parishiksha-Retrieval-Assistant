# Failure Modes Analysis

1. **Chunk Boundary Failures**  
   Worked examples split across chunks → missing solution in retrieval.  
   Mitigation: Smart chunking with example preservation.

2. **Cross-Chapter Lexical Overlap**  
   BM25 retrieves content from wrong chapter due to shared terms (force, acceleration).  
   Mitigation: Add chapter metadata filtering.

3. **Weak Grounding on Edge Cases**  
   Early prompt versions caused synthesis on out-of-scope questions.  
   Mitigation: Strict refusal instruction + exact refusal phrase.

These are grounded in actual evaluation results.