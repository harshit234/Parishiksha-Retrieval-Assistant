# Retrieval Misses — Top-1 Failures

**Retriever**: BM25Okapi + chapter topic-boost (`src/retrieval.py`)
**Corpus version**: `chunks.json` v2
**Evaluated**: 2026-04-30 | Manual review

---

## Miss 1 — qid 9

**Query**: *"What happens to the velocity of an object moving in a uniform circular path?"*

**Wrong top-1 chunk returned** (chunk_id = 4, content_type: `definition`, topic: speed and velocity):

```
Speed and Velocity:
- Speed: The rate at which an object covers distance... scalar quantity.
- Velocity: The rate of change of displacement... vector quantity.
```

**Expected chunk**: chunk_id = 9 — Uniform Circular Motion (speed is constant but velocity direction changes continuously).

**Diagnosis**: BM25 latched onto the high-frequency keyword `velocity` and ranked the generic speed/velocity definition chunk above the circular-motion chunk that actually answers the directional-change question.

---

## Miss 2 — qid 10

**Query**: *"Calculate the recoil velocity of a 5 kg gun that fires a 0.05 kg bullet at 200 m/s."*

**Wrong top-1 chunk returned** (chunk_id = 12, content_type: `law`, topic: Newton's third law):

```
Chapter 8 – Newton's Third Law of Motion:
...Examples:
- Recoil of a gun when fired
- Rocket propulsion...
```

**Expected chunk**: chunk_id = 20 — Conservation of Momentum worked example containing the full calculation `v_gun = –(0.05 × 200) / 5 = –2 m/s`.

**Diagnosis**: The words `gun` and `recoil` appear as illustrative examples inside the Newton's 3rd law chunk, causing BM25 to prefer a concept-mention chunk over the worked-solution chunk that contains the arithmetic the question actually requires.

---

## Miss 3 — Q6 (evaluation_results.md)

**Query**: *"What are the three equations of motion?"*

**Wrong top-1 chunk returned** (non-contact forces / law of inertia chunk):

```
2. Non-Contact Forces:
   - Gravitational Force: Force of attraction between masses
   - Magnetic Force: Force between magnetic poles
   - Electrostatic Force: Force between charged particles

Newton's Laws of Motion Applied:
Law of Inertia:
Objects tend to maintain their state of motion. A heavier...
```

**Expected chunk**: Kinematic Equations chunk — `v = u + at`, `s = ut + ½at²`, `v² = u² + 2as`.

**Diagnosis**: The equations chunk is symbol-heavy with almost no prose, so BM25 finds near-zero term overlap and falls back to a longer narrative chunk where the word `motion` appears more frequently.

---

## Summary

| # | Query (short) | Wrong chunk | Root cause |
|---|---------------|-------------|------------|
| 1 | velocity in circular path | speed & velocity definition (chunk 4) | Keyword collision on `velocity` |
| 2 | gun recoil calculation | Newton's 3rd law examples (chunk 12) | Concept-mention ranked above worked solution |
| 3 | three equations of motion | non-contact forces / inertia narrative | Symbol-heavy chunk penalised by BM25 IDF |
