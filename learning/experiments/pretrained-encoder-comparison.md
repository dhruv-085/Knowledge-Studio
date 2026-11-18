# Pretrained encoder comparison

## Hypothesis

A pretrained sentence encoder should retrieve paraphrases that BM25 cannot
match because they share no important words. Combining BM25 with the
pretrained encoder should preserve exact-identifier retrieval while adding
semantic coverage.

## Experiment

- Corpus: `data/phase-1-example.txt`
- Evaluation set: 18 manually reviewed questions in
  `data/retrieval-evaluation.json`
- Dense model: `all-MiniLM-L6-v2`
- Fusion: reciprocal rank fusion with the existing rank constant of 60
- Candidate depth: 5
- Reported depths: 1, 2, and 5

## Results

| Strategy | Recall@1 | Precision@1 | MRR | Recall@5 |
|---|---:|---:|---:|---:|
| BM25 | 0.833 | 0.833 | 0.833 | 0.833 |
| Teaching semantic | 0.611 | 0.611 | 0.611 | 0.611 |
| Pretrained semantic | 1.000 | 1.000 | 1.000 | 1.000 |
| Teaching hybrid | 0.889 | 0.889 | 0.889 | 0.889 |
| BM25 + pretrained hybrid | 1.000 | 1.000 | 1.000 | 1.000 |

The pretrained encoder and pretrained hybrid both achieved Recall@2 1.000
and Precision@2 0.500. Average cross-encoder reranking latency, retained as
context from the existing experiment, was 43.98 ms/query; this is not the
latency of the bi-encoder retrieval path.

## Conclusion

The result supports the hypothesis on this fixture. BM25 is useful for exact
terms such as `MAX_RETRIES`, while the pretrained encoder handles paraphrases
such as questions about retry limits without using the original wording.

Hybrid retrieval is still the safer first-stage design because it combines
lexical and semantic evidence. However, this corpus is only three passages,
so the hybrid tie is not proof that fusion always improves ranking.

## Important limitation

The pretrained model downloads model weights and is much larger than the
teaching embedder. A production system would need model caching, startup
management, latency measurement, and a larger evaluation corpus.
