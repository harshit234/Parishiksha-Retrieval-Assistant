from transformers import GPT2Tokenizer, BertTokenizer
import json
import os

def compare_tokenizers():

    text_samples = [
        "The acceleration due to gravity is denoted by g.",
        "Example 1: A car moving with uniform velocity.",
        "Newton's second law: Force = mass x acceleration",
        "photosynthesis is a process in plants",
        "specific heat capacity of water is 4184 J/kg/K"
    ]

    science_terms = ["velocity", "acceleration", "work", "energy", "photosynthesis"]

    print("Loading tokenizers...")
    gpt2 = GPT2Tokenizer.from_pretrained("gpt2")
    bert = BertTokenizer.from_pretrained("bert-base-uncased")
    print("Done.\n")

    # ── PASSAGE COMPARISON ──────────────────────────────────────────────────
    print("=" * 75)
    print(f"  {'TEXT':<46} {'GPT-2':>5} {'BERT':>5} {'DIFF':>5}")
    print("=" * 75)

    results = []
    for text in text_samples:
        g_toks = gpt2.tokenize(text)
        b_toks = bert.tokenize(text)
        diff   = len(g_toks) - len(b_toks)
        sign   = "+" if diff > 0 else ""
        preview = text[:45] + "…" if len(text) > 46 else text
        print(f"  {preview:<46} {len(g_toks):>5} {len(b_toks):>5} {sign+str(diff):>5}")
        results.append({
            "text":        text,
            "gpt2_count":  len(g_toks),
            "gpt2_tokens": g_toks,
            "bert_count":  len(b_toks),
            "bert_tokens": b_toks,
            "diff":        diff
        })

    print("=" * 75)

    # ── DETAILED BREAKDOWN ───────────────────────────────────────────────────
    print("\n── DETAILED BREAKDOWN ──\n")
    for r in results:
        print(f"TEXT  : {r['text']}")
        print(f"GPT-2 ({r['gpt2_count']} tokens) : {r['gpt2_tokens']}")
        print(f"BERT  ({r['bert_count']} tokens) : {r['bert_tokens']}")
        if r["diff"] > 0:
            print(f"NOTE  : GPT-2 uses {r['diff']} MORE token(s) than BERT")
        elif r["diff"] < 0:
            print(f"NOTE  : BERT uses {abs(r['diff'])} MORE token(s) than GPT-2")
        else:
            print("NOTE  : Same token count")
        print()

    # ── SCIENTIFIC TERM SPLIT ────────────────────────────────────────────────
    print("── SCIENTIFIC TERM SPLIT ──\n")
    print(f"  {'TERM':<20} {'GPT-2 SPLIT':<35} {'BERT SPLIT'}")
    print("  " + "-" * 70)

    term_results = []
    for term in science_terms:
        g = gpt2.tokenize(term)
        b = bert.tokenize(term)
        print(f"  {term:<20} {str(g):<35} {str(b)}")
        term_results.append({
            "term":        term,
            "gpt2_tokens": g,
            "bert_tokens": b
        })

    # ── SUMMARY ─────────────────────────────────────────────────────────────
    avg_gpt2 = sum(r["gpt2_count"] for r in results) / len(results)
    avg_bert = sum(r["bert_count"] for r in results) / len(results)
    overhead = ((avg_bert - avg_gpt2) / avg_gpt2) * 100

    print("\n── SUMMARY ──\n")
    print(f"  GPT-2 average tokens : {avg_gpt2:.1f}")
    print(f"  BERT  average tokens : {avg_bert:.1f}")
    print(f"  BERT overhead        : +{overhead:.0f}% more tokens than GPT-2")
    print()
    print("  DECISION:")
    print("  → Use GPT-2 BPE for chunk SIZE measurement")
    print("    (preserves case, stable on NCERT mixed-case headings)")
    print("  → Use re.findall(r'\\w+', text.lower()) for BM25 index AND query")
    print("    (identical tokenization both sides = no silent score corruption)")

    # ── SAVE OUTPUT ──────────────────────────────────────────────────────────
    os.makedirs("outputs", exist_ok=True)   # creates folder if missing

    output = {
        "passage_comparison": results,
        "scientific_terms":   term_results,
        "summary": {
            "avg_gpt2_tokens": round(avg_gpt2, 1),
            "avg_bert_tokens": round(avg_bert, 1),
            "bert_overhead_pct": round(overhead, 1),
            "decision": "GPT-2 for chunk sizing; re.findall for BM25"
        }
    }

    with open("outputs/tokenizer_comparison.json", "w") as f:
        json.dump(output, f, indent=2)

    print("\n✓ Results saved to outputs/tokenizer_comparison.json")
    return results


if __name__ == "__main__":
    compare_tokenizers()


Loading tokenizers...
Done.

===========================================================================
  TEXT                                           GPT-2  BERT  DIFF
===========================================================================
  The acceleration due to gravity is denoted by…    11    10    +1
  Example 1: A car moving with uniform velocity.    10    10     0
  Newton's second law: Force = mass x accelerat…    11    11     0
  photosynthesis is a process in plants              7     8    -1
  specific heat capacity of water is 4184 J/kg/K    13    14    -1
===========================================================================

── DETAILED BREAKDOWN ──

TEXT  : The acceleration due to gravity is denoted by g.
GPT-2 (11 tokens) : ['The', 'Ġacceleration', 'Ġdue', 'Ġto', 'Ġgravity', 'Ġis', 'Ġden', 'oted', 'Ġby', 'Ġg', '.']
BERT  (10 tokens) : ['the', 'acceleration', 'due', 'to', 'gravity', 'is', 'denoted', 'by', 'g', '.']
NOTE  : GPT-2 uses 1 MORE token(s) than BERT

TEXT  : Example 1: A car moving with uniform velocity.
GPT-2 (10 tokens) : ['Example', 'Ġ1', ':', 'ĠA', 'Ġcar', 'Ġmoving', 'Ġwith', 'Ġuniform', 'Ġvelocity', '.']
BERT  (10 tokens) : ['example', '1', ':', 'a', 'car', 'moving', 'with', 'uniform', 'velocity', '.']
NOTE  : Same token count

TEXT  : Newton's second law: Force = mass x acceleration
GPT-2 (11 tokens) : ['New', 'ton', "'s", 'Ġsecond', 'Ġlaw', ':', 'ĠForce', 'Ġ=', 'Ġmass', 'Ġx', 'Ġacceleration']
BERT  (11 tokens) : ['newton', "'", 's', 'second', 'law', ':', 'force', '=', 'mass', 'x', 'acceleration']
NOTE  : Same token count

TEXT  : photosynthesis is a process in plants
GPT-2 (7 tokens) : ['photos', 'ynthesis', 'Ġis', 'Ġa', 'Ġprocess', 'Ġin', 'Ġplants']
BERT  (8 tokens) : ['photos', '##yn', '##thesis', 'is', 'a', 'process', 'in', 'plants']
NOTE  : BERT uses 1 MORE token(s) than GPT-2

TEXT  : specific heat capacity of water is 4184 J/kg/K
GPT-2 (13 tokens) : ['specific', 'Ġheat', 'Ġcapacity', 'Ġof', 'Ġwater', 'Ġis', 'Ġ4', '184', 'ĠJ', '/', 'kg', '/', 'K']
BERT  (14 tokens) : ['specific', 'heat', 'capacity', 'of', 'water', 'is', '41', '##8', '##4', 'j', '/', 'kg', '/', 'k']
NOTE  : BERT uses 1 MORE token(s) than GPT-2

── SCIENTIFIC TERM SPLIT ──

  TERM                 GPT-2 SPLIT                         BERT SPLIT
  ----------------------------------------------------------------------
  velocity             ['vel', 'ocity']                    ['velocity']
  acceleration         ['ac', 'celer', 'ation']            ['acceleration']
  work                 ['work']                            ['work']
  energy               ['energy']                          ['energy']
  photosynthesis       ['photos', 'ynthesis']              ['photos', '##yn', '##thesis']

── SUMMARY ──

  GPT-2 average tokens : 10.4
  BERT  average tokens : 10.6
  BERT overhead        : +2% more tokens than GPT-2

  DECISION:
  → Use GPT-2 BPE for chunk SIZE measurement
    (preserves case, stable on NCERT mixed-case headings)
  → Use re.findall(r'\w+', text.lower()) for BM25 index AND query
    (identical tokenization both sides = no silent score corruption)

✓ Results saved to outputs/tokenizer_comparison.json
