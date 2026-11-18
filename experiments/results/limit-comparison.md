# Retrieval limit comparison

Command:

```text
python -m rag_assistant.limit_experiment
```

The experiment ran 18 manually reviewed questions with the pretrained encoder,
the existing hybrid retrieval pipeline, and the deterministic local extractive
generator.

Definitions:

- Answer correctness: the first retrieved passage is expected and the answer was not refused.
- Irrelevant passages: retrieved passage IDs not expected for that question.
- Citation correctness: every attached citation refers to expected evidence.

| Limit | Answer correctness | Average irrelevant passages | Citation correctness | Refusal rate |
|---:|---:|---:|---:|---:|
| 1 | 1.000 | 0.000 | 1.000 | 0.000 |
| 2 | 1.000 | 1.000 | 0.000 | 0.000 |
| 3 | 1.000 | 1.333 | 0.000 | 0.000 |

On this small three-passage fixture, increasing the context limit did not
improve answer correctness because the best passage was already first. It did
increase irrelevant evidence, and the current generator attaches citations for
every usable evidence item. This is evidence for investigating citation
selection, not proof that limit 1 is best for larger multi-document questions.

Complete per-question measurements are in
`experiments/results/limit-comparison.json`.
