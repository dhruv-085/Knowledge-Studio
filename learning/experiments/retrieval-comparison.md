# Retrieval strategy comparison

## Hypothesis

Keyword search should be strongest for exact identifiers such as
`MAX_RETRIES`. Semantic search should be strongest for paraphrases such as a
question about remaining logged in without activity. Hybrid retrieval may
improve recall by combining both result lists, but rank fusion could also
promote a passage that receives weak support from both methods.

## Experiment

Input: `data/phase-1-example.txt`

Evaluation questions and expected passage IDs are stored in
`data/retrieval-evaluation.json`.

Configuration:

- evaluation questions: 9;
- keyword result depth: 5;
- semantic result depth: 5;
- hybrid result depth: 5;
- fusion: reciprocal rank fusion with rank constant 60;
- semantic model: the current five-dimension teaching embedder.

Metrics:

- Recall@5: fraction of expected passage IDs found in the first five results;
- Precision@5: fraction of the five result slots containing expected passages;
- MRR: mean reciprocal rank of the first expected passage.

Command:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m rag_assistant.retrieval_experiment
```

## Observed results

| Strategy | Recall@5 | Precision@5 | MRR |
|---|---:|---:|---:|
| Keyword | 0.889 | 0.178 | 0.704 |
| Semantic | 0.667 | 0.133 | 0.667 |
| Hybrid | 0.889 | 0.178 | 0.833 |

Question-level behavior:

- Hybrid matched keyword retrieval's Recall@5 and improved MRR over both
  individual strategies on this expanded fixture.
- Hybrid did not achieve perfect Recall@5: the question about the retry limit
  was phrased broadly enough that keyword retrieval returned the session
  passage and the teaching embedder produced no result.
- The teaching embedder skipped passage 3 for semantic search because its
  hand-written vocabulary does not contain the configuration terms.
- Precision@5 is low partly because the source document contains only three
  passages, while the requested result depth is five. This is a limitation of
  the tiny fixture, not a production-quality precision estimate.

## Broader hybrid follow-up

The first pipeline used lexical search only as a targeted fallback when the
teaching embedder failed. The follow-up runs lexical search for every query and
fuses it with semantic results. Generic query terms including `system` and
`service` are ignored as lexical evidence, while exact identifiers remain
searchable.

The 18-question run produced:

| Strategy | Recall@1 | Precision@1 | MRR |
|---|---:|---:|---:|
| Previous hybrid | 0.778 | 0.778 | 0.833 |
| Broader hybrid | 0.889 | 0.889 | 0.889 |

At depth 2, Recall remained 0.889 and Precision remained 0.444. Two questions
still produced no candidates because the toy teaching vocabulary and the
lexical terms did not overlap with the retry passage. The generic system/model
question continued to refuse, which is the desired guardrail behavior.

The cross-encoder was not better on this tiny corpus and averaged 146.16
ms/query in this run. These measurements are fixture-specific and do not
justify a general claim about hybrid retrieval or cross-encoder quality.

## Conclusion

On this expanded but still tiny fixture, hybrid preserved the best observed
Recall@5 (0.889) and produced the best MRR (0.833). This supports using hybrid
as a high-recall first-stage retriever, but it is not evidence that hybrid is
universally better.

The fusion experiment also exposed a limitation in the current semantic
implementation: the hand-written teaching vocabulary is useful for learning
vector flow, but it is not broad enough to represent every passage. A
pretrained embedding model should be evaluated separately rather than treated
as equivalent to this toy model.

## Next discovery

Before reranking, investigate the failed retry-limit paraphrase and compare
the candidate ordering at a larger retrieval depth. Then introduce a
reranker and measure whether it improves MRR and Precision without reducing
Recall@5.
