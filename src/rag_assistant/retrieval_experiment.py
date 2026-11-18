"""Compare retrieval strategies with recall, precision, and MRR."""

import json
from pathlib import Path
from time import perf_counter
from typing import Any

from .bm25 import BM25Index
from .embeddings import PretrainedSentenceEncoder, TeachingEmbedder
from .hybrid_search import reciprocal_rank_fusion
from .keyword_search import KeywordIndex, load_text_file, split_into_passages
from .reranker import rerank
from .cross_encoder_reranker import load_cross_encoder, rerank_with_cross_encoder
from .semantic_search import build_semantic_index


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCUMENT_PATH = PROJECT_ROOT / "data" / "phase-1-example.txt"
EVALUATION_PATH = PROJECT_ROOT / "data" / "retrieval-evaluation.json"


def load_cases(path: Path) -> list[dict[str, Any]]:
    """Load manually reviewed questions and expected evidence IDs."""

    return json.loads(path.read_text(encoding="utf-8"))


def contains_expected(result_ids: list[int], expected_ids: list[int]) -> bool:
    """Return whether a result list contains at least one expected passage."""

    return any(result_id in expected_ids for result_id in result_ids)


def recall_at_k(
    result_ids: list[int],
    expected_ids: list[int],
    k: int,
) -> float:
    """Measure the fraction of expected passages found in the top k."""

    if k <= 0:
        raise ValueError("k must be greater than zero")
    if not expected_ids:
        raise ValueError("expected_ids must not be empty")

    expected = set(expected_ids)
    retrieved = set(result_ids[:k])
    return len(expected.intersection(retrieved)) / len(expected)


def precision_at_k(
    result_ids: list[int],
    expected_ids: list[int],
    k: int,
) -> float:
    """Measure the fraction of the top-k slots containing expected passages."""

    if k <= 0:
        raise ValueError("k must be greater than zero")
    if not expected_ids:
        raise ValueError("expected_ids must not be empty")

    expected = set(expected_ids)
    relevant_count = sum(result_id in expected for result_id in result_ids[:k])
    return relevant_count / k


def reciprocal_rank(result_ids: list[int], expected_ids: list[int]) -> float:
    """Return the reciprocal rank of the first expected passage, or zero."""

    if not expected_ids:
        raise ValueError("expected_ids must not be empty")

    expected = set(expected_ids)

    for rank, result_id in enumerate(result_ids, start=1):
        if result_id in expected:
            return 1 / rank

    return 0.0


def mean_metrics(
    result_ids_by_case: list[list[int]],
    expected_ids_by_case: list[list[int]],
    k: int,
) -> dict[str, float]:
    """Average retrieval metrics at one final output depth."""

    if len(result_ids_by_case) != len(expected_ids_by_case):
        raise ValueError("result and expected case counts must match")
    if not result_ids_by_case:
        raise ValueError("at least one evaluation case is required")

    return {
        "recall": sum(
            recall_at_k(result_ids, expected_ids, k)
            for result_ids, expected_ids in zip(
                result_ids_by_case, expected_ids_by_case, strict=True
            )
        )
        / len(result_ids_by_case),
        "precision": sum(
            precision_at_k(result_ids, expected_ids, k)
            for result_ids, expected_ids in zip(
                result_ids_by_case, expected_ids_by_case, strict=True
            )
        )
        / len(result_ids_by_case),
        "mrr": sum(
            reciprocal_rank(result_ids, expected_ids)
            for result_ids, expected_ids in zip(
                result_ids_by_case, expected_ids_by_case, strict=True
            )
        )
        / len(result_ids_by_case),
    }


def main() -> int:
    document_text = load_text_file(DOCUMENT_PATH)
    passages = split_into_passages(document_text)
    keyword_index = KeywordIndex(passages)
    bm25_index = BM25Index(passages)
    teaching_embedder = TeachingEmbedder()
    teaching_index, teaching_skipped_ids = build_semantic_index(
        passages,
        teaching_embedder,
    )
    pretrained_encoder = PretrainedSentenceEncoder()
    pretrained_index, pretrained_skipped_ids = build_semantic_index(
        passages,
        pretrained_encoder,
    )
    cases = load_cases(EVALUATION_PATH)

    strategies = (
        "guarded-lexical",
        "bm25",
        "teaching-semantic",
        "pretrained-semantic",
        "teaching-hybrid",
        "pretrained-hybrid",
        "bm25-teaching-hybrid",
        "bm25-pretrained-hybrid",
        "teaching-reranker",
        "cross-encoder",
    )
    candidate_limit = 5
    final_depths = (1, 2, 5)
    result_ids_by_strategy = {strategy: [] for strategy in strategies}
    expected_ids_by_case = []
    teaching_latency = 0.0
    cross_encoder = load_cross_encoder()
    cross_encoder_latency = 0.0

    print("Retrieval strategy comparison")
    print("=============================")
    print(f"document={DOCUMENT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"questions={len(cases)}")
    print()

    for case in cases:
        question = case["question"]
        expected_ids = case["expected_passage_ids"]
        keyword_results = keyword_index.search(question, limit=candidate_limit)
        bm25_results = bm25_index.search(question, limit=candidate_limit)

        try:
            teaching_query_vector = teaching_embedder.embed(question)
            teaching_semantic_results = teaching_index.search(
                teaching_query_vector,
                limit=candidate_limit,
            )
        except ValueError:
            teaching_semantic_results = []

        pretrained_query_vector = pretrained_encoder.embed(question)
        pretrained_results = pretrained_index.search(
            pretrained_query_vector,
            limit=candidate_limit,
        )

        teaching_hybrid_results = reciprocal_rank_fusion(
            keyword_results,
            teaching_semantic_results,
            limit=candidate_limit,
        )
        pretrained_hybrid_results = reciprocal_rank_fusion(
            keyword_results,
            pretrained_results,
            limit=candidate_limit,
        )
        bm25_teaching_hybrid_results = reciprocal_rank_fusion(
            bm25_results,
            teaching_semantic_results,
            limit=candidate_limit,
        )
        bm25_pretrained_hybrid_results = reciprocal_rank_fusion(
            bm25_results,
            pretrained_results,
            limit=candidate_limit,
        )

        teaching_started = perf_counter()
        teaching_reranked_results = rerank(
            question,
            teaching_hybrid_results,
            limit=candidate_limit,
        )
        teaching_latency += perf_counter() - teaching_started

        cross_encoder_started = perf_counter()
        cross_encoder_results = rerank_with_cross_encoder(
            question,
            teaching_hybrid_results,
            cross_encoder,
            limit=candidate_limit,
        )
        cross_encoder_latency += perf_counter() - cross_encoder_started

        result_ids = {
            "guarded-lexical": [
                result.passage.passage_id for result in keyword_results
            ],
            "bm25": [result.passage.passage_id for result in bm25_results],
            "teaching-semantic": [
                result.record.record_id for result in teaching_semantic_results
            ],
            "pretrained-semantic": [
                result.record.record_id for result in pretrained_results
            ],
            "teaching-hybrid": [
                result.passage.passage_id for result in teaching_hybrid_results
            ],
            "pretrained-hybrid": [
                result.passage.passage_id
                for result in pretrained_hybrid_results
            ],
            "bm25-teaching-hybrid": [
                result.passage.passage_id
                for result in bm25_teaching_hybrid_results
            ],
            "bm25-pretrained-hybrid": [
                result.passage.passage_id
                for result in bm25_pretrained_hybrid_results
            ],
            "teaching-reranker": [
                result.passage.passage_id for result in teaching_reranked_results
            ],
            "cross-encoder": [
                result.passage.passage_id for result in cross_encoder_results
            ],
        }
        expected_ids_by_case.append(expected_ids)

        print(f"Question: {question}")
        print(f"Expected passage(s): {expected_ids}")
        for strategy in strategies:
            ids = result_ids[strategy]
            result_ids_by_strategy[strategy].append(ids)
            print(f"  {strategy:17} candidates={ids}")
        print()

    print("Summary")
    print("=======")
    for depth in final_depths:
        print(f"Final depth: {depth}")
        for strategy in strategies:
            metrics = mean_metrics(
                result_ids_by_strategy[strategy],
                expected_ids_by_case,
                depth,
            )
            print(
                f"  {strategy:17} "
                f"Recall@{depth}={metrics['recall']:.3f} "
                f"Precision@{depth}={metrics['precision']:.3f} "
                f"MRR={metrics['mrr']:.3f}"
            )

    print()
    print(
        f"Average teaching reranker latency: "
        f"{teaching_latency / len(cases) * 1000:.2f} ms/query"
    )
    print(
        f"Average cross-encoder latency: "
        f"{cross_encoder_latency / len(cases) * 1000:.2f} ms/query"
    )

    if teaching_skipped_ids or pretrained_skipped_ids:
        print(
            "Semantic indexes skipped passages: "
            f"teaching={teaching_skipped_ids}, "
            f"pretrained={pretrained_skipped_ids}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
