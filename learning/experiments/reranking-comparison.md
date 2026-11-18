# Reranking comparison

## Hypothesis

A second-stage reranker should improve ordering when the first-stage hybrid
retriever already contains the relevant passage. It should improve MRR and may
improve precision at a smaller output depth, but it cannot improve recall if
the relevant passage was never retrieved.

## Experiment

Input: `data/phase-1-example.txt`

Configuration:

- evaluation questions: 9;
- first-stage retriever: reciprocal-rank-fusion hybrid search;
- candidate depth: 5;
- final result depth: 5;
- reranker: transparent non-stopword term overlap with an exact-identifier
  bonus;
- model dependency: none.

The reranker receives only `HybridSearchResult` candidates. It does not search
the corpus again. Its score is used only to reorder those candidates.

## Observed results

| Strategy | Recall@5 | Precision@5 | MRR |
|---|---:|---:|---:|
| Hybrid | 0.889 | 0.178 | 0.833 |
| Hybrid + reranker | 0.889 | 0.178 | 0.889 |

The reranker moved the relevant retry-latency passage from rank 2 to rank 1.
Recall@5 did not decrease. Precision@5 did not change because the reranker
reordered the same candidate set, and this fixture contains only three source
passages while the metric requests five result slots.

## Conclusion

The experiment supports the expected role of reranking on this tiny fixture:
it improved ordering, measured by MRR, while preserving candidate coverage.
It does not demonstrate broad language understanding. For example, the
transparent lexical reranker cannot independently understand every paraphrase;
it relies on the first-stage hybrid scores when its pairwise term overlap is
zero.

## Precision at smaller output depths

The next experiment expanded the fixture from nine to eighteen questions by
adding three harder paraphrases for each source passage. The candidate depth
remained five, and the final rankings were measured at depths 1, 2, and 5.
It also compared the teaching reranker with the pretrained
`cross-encoder/ms-marco-MiniLM-L6-v2` model.

The cross-encoder receives each `(question, candidate passage)` pair and
scores the pair jointly. It does not search the corpus again. This is why it
can improve ordering but cannot recover passage 3 for the retry-limit
paraphrase: hybrid retrieval never supplied passage 3 as a candidate.

### Observed results on the expanded set

| Strategy | Recall@1 | Precision@1 | MRR | Recall@2 | Precision@2 |
|---|---:|---:|---:|---:|---:|
| Hybrid | 0.778 | 0.778 | 0.833 | 0.889 | 0.444 |
| Hybrid + teaching reranker | 0.889 | 0.889 | 0.889 | 0.889 | 0.444 |
| Hybrid + cross-encoder | 0.889 | 0.889 | 0.889 | 0.889 | 0.444 |

At depth 5, all three strategies had Recall 0.889 and Precision 0.178.
Average measured reranking time was 0.06 ms/query for the teaching reranker
and 24.96 ms/query for the cross-encoder on this local run.

The expanded questions did not change the aggregate metrics. One difficult
retry paraphrase produced no candidates from the first-stage retriever because
the teaching embedder did not recognize its vocabulary. Both rerankers
therefore had nothing to score for that case. This is a concrete example of
the first-stage recall boundary rather than evidence that the paraphrase was
easy.

### Conclusion

On this tiny three-passage fixture, the pretrained cross-encoder still tied
the teaching reranker rather than demonstrating a quality advantage, even
after adding harder paraphrases. The teaching reranker was much cheaper and
easier to inspect. This is not evidence that the teaching reranker is
generally as capable: the corpus is too small, and several questions remain
easy for the first-stage retriever. A domain-sized evaluation set built from
real target documents is needed before making a production quality claim.

The experiment does demonstrate two important boundaries:

1. Reranking improved top-1 ordering when the relevant candidate was already
   present.
2. Reranking cannot fix first-stage retrieval misses.
