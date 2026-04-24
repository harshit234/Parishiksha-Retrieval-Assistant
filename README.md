# PariShiksha - Retrieval-Ready NCERT Study Assistant

### Base (Required)
- ✅ PDF Extraction (Chapters 8 & 9)
- ✅ Tokenizer Comparison
- ✅ Smart Chunking (512 tokens + overlap + example preservation)
- ✅ BM25 Retrieval with Metadata
- ✅ Grounded Generation with Grok API
- ✅ Evaluation (20 questions)
- ✅ Reflection

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


## Key Files
- `src/generation.py` - Grok API with grounding
- `src/teacher_mode.py` - Citation support


## Evaluation Results
- Correctness: 15/20
- Grounding: 19/20
- Appropriate Refusals: 4/4


