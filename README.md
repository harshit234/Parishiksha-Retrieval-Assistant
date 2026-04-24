# PariShiksha - Retrieval-Ready NCERT Study Assistant

### Base (Required)
- ✅ PDF Extraction (Chapters 8 & 9)
- ✅ Tokenizer Comparison
- ✅ Smart Chunking (512 tokens + overlap + example preservation)
- ✅ BM25 Retrieval with Metadata
- ✅ Grounded Generation with Grok API
- ✅ Evaluation (20 questions)
- ✅ Reflection

### Stretch
- ✅ Model Family Comparison (RoBERTa, Flan-T5, Grok)
- ✅ Chunking Experiment (256 vs 512 tokens)
- ✅ Attention Inspection (documented in notebook)

### Advanced
- ✅ Dense Retrieval (all-MiniLM-L6-v2)
- ✅ Guardrails (out-of-scope, prompt injection, input validation)
- ✅ failure_modes.md (400+ words, grounded in eval results)

### Open (Bonus)
- ✅ Teacher Mode: Answers with citations (src/teacher_mode.py)

## Quick Start

1. Set API Key:
   ```bash
   export XAI_API_KEY="xai-your-key"
   ```

2. Run:
   ```bash
   python src/corpus.py
   python src/chunking.py
   python src/evaluation.py
   ```

3. Run Model Comparison:
   ```bash
   jupyter notebook experiments/03_model_comparison.ipynb
   ```

## Key Files
- `src/generation.py` - Grok API with grounding
- `src/guardrails.py` - Safety layer
- `src/dense_retrieval.py` - Embedding-based retrieval
- `src/teacher_mode.py` - Citation support
- `failure_modes.md` - Production failure analysis
- `experiments/03_model_comparison.ipynb` - Stretch comparison

## Evaluation Results
- Correctness: 15/20
- Grounding: 19/20
- Appropriate Refusals: 4/4


