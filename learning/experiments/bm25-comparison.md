# BM25 comparison

## Hypothesis

BM25 should rank lexical matches more usefully than the guarded one-point-per-term matcher because it considers term rarity, repeated terms, and passage length.

## Experiment

- Same 18 manually reviewed questions.
- Same passages and tokenizer.
- Same guarded stopword list, so exact identifiers remain searchable.
- Compared guarded lexical search, BM25, guarded hybrid, and BM25 hybrid.
- Semantic results and RRF settings remained unchanged.

## Results

Run:

```powershell
$env:PYTHONPATH="src"
.venv\Scripts\python.exe -m rag_assistant.retrieval_experiment
```

Measured on the current 18-question, three-passage fixture:

| Strategy | Recall@1 | Precision@1 | MRR | Recall@5 | Precision@5 |
|---|---:|---:|---:|---:|---:|
| Guarded lexical | 0.833 | 0.833 | 0.833 | 0.833 | 0.167 |
| BM25 | 0.833 | 0.833 | 0.833 | 0.833 | 0.167 |
| Guarded hybrid | 0.889 | 0.889 | 0.889 | 0.889 | 0.178 |
| BM25 hybrid | 0.889 | 0.889 | 0.889 | 0.889 | 0.178 |

The BM25 and guarded lexical rankings were identical for this fixture.

## Interpretation

BM25 did not improve this fixture because each lexical match was already
unambiguous. It cannot retrieve a passage when the query and passage share no
guarded lexical terms, so semantic retrieval is still needed for paraphrases.
The hybrid result remained better than either lexical-only strategy because
the teaching embedder supplied evidence for the paraphrased session question.

The next useful experiment needs more passages with repeated terms, different
lengths, and competing partial matches. Those conditions are where BM25's term
rarity and length normalization can change ordering.
