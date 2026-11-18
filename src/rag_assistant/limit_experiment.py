"""Measure answer quality as the final retrieved passage limit changes."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .document_loader import load_document
from .embeddings import PretrainedSentenceEncoder
from .multi_document_rag import DocumentInput, MultiDocumentRagPipeline
from .retrieval_experiment import load_cases


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCUMENT_PATH = PROJECT_ROOT / "data" / "phase-1-example.txt"
EVALUATION_PATH = PROJECT_ROOT / "data" / "retrieval-evaluation.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "experiments" / "results" / "limit-comparison.json"


@dataclass(frozen=True)
class LimitCaseResult:
    case_id: str
    question: str
    limit: int
    expected_passage_ids: tuple[int, ...]
    retrieved_passage_ids: tuple[int, ...]
    cited_passage_ids: tuple[int, ...]
    answer_correct: bool
    irrelevant_passages: int
    citations_correct: bool
    refused: bool


def evaluate_case(
    pipeline: MultiDocumentRagPipeline,
    case: dict[str, Any],
    limit: int,
) -> LimitCaseResult:
    """Run one manually reviewed question at one output limit."""

    response = pipeline.answer(
        (DocumentInput(
            document_id="phase-1-example",
            document_name=DOCUMENT_PATH.name,
            text=DOCUMENT_PATH.read_text(encoding="utf-8"),
            source_path=str(DOCUMENT_PATH),
        ),),
        case["question"],
    )
    expected = tuple(case["expected_passage_ids"])
    retrieved = tuple(item.passage_id for item in response.context.evidence)
    cited = tuple(citation.passage_id for citation in response.answer.citations)
    expected_set = set(expected)

    return LimitCaseResult(
        case_id=case["id"],
        question=case["question"],
        limit=limit,
        expected_passage_ids=expected,
        retrieved_passage_ids=retrieved,
        cited_passage_ids=cited,
        answer_correct=(
            not response.answer.refused
            and bool(retrieved)
            and retrieved[0] in expected_set
        ),
        irrelevant_passages=sum(
            passage_id not in expected_set for passage_id in retrieved
        ),
        citations_correct=bool(cited) and all(
            passage_id in expected_set for passage_id in cited
        ),
        refused=response.answer.refused,
    )


def run_experiment(
    limits: tuple[int, ...] = (1, 2, 3),
) -> dict[str, Any]:
    """Run the comparison and return JSON-serializable measurements."""

    if not limits or any(limit <= 0 for limit in limits):
        raise ValueError("limits must contain only positive values")

    document_text = DOCUMENT_PATH.read_text(encoding="utf-8")
    document = DocumentInput(
        document_id="phase-1-example",
        document_name=DOCUMENT_PATH.name,
        text=document_text,
        source_path=str(DOCUMENT_PATH),
    )
    cases = load_cases(EVALUATION_PATH)
    results: list[LimitCaseResult] = []

    for limit in limits:
        pipeline = MultiDocumentRagPipeline(
            max_passages=limit,
            embedder=PretrainedSentenceEncoder(),
        )
        for case in cases:
            response = pipeline.answer((document,), case["question"])
            expected = tuple(case["expected_passage_ids"])
            retrieved = tuple(item.passage_id for item in response.context.evidence)
            cited = tuple(citation.passage_id for citation in response.answer.citations)
            expected_set = set(expected)
            results.append(
                LimitCaseResult(
                    case_id=case["id"],
                    question=case["question"],
                    limit=limit,
                    expected_passage_ids=expected,
                    retrieved_passage_ids=retrieved,
                    cited_passage_ids=cited,
                    answer_correct=(
                        not response.answer.refused
                        and bool(retrieved)
                        and retrieved[0] in expected_set
                    ),
                    irrelevant_passages=sum(
                        passage_id not in expected_set for passage_id in retrieved
                    ),
                    citations_correct=bool(cited) and all(
                        passage_id in expected_set for passage_id in cited
                    ),
                    refused=response.answer.refused,
                )
            )

    summary: dict[str, dict[str, float]] = {}
    for limit in limits:
        subset = [result for result in results if result.limit == limit]
        summary[str(limit)] = {
            "answer_correct_rate": sum(item.answer_correct for item in subset) / len(subset),
            "average_irrelevant_passages": sum(item.irrelevant_passages for item in subset) / len(subset),
            "citation_correct_rate": sum(item.citations_correct for item in subset) / len(subset),
            "refusal_rate": sum(item.refused for item in subset) / len(subset),
        }

    return {
        "document": str(DOCUMENT_PATH.relative_to(PROJECT_ROOT)),
        "evaluation_questions": len(cases),
        "limits": list(limits),
        "definitions": {
            "answer_correct": "The first retrieved passage is one of the manually expected passages and the answer was not refused.",
            "irrelevant_passages": "Retrieved passages whose IDs are not manually expected for the question.",
            "citations_correct": "Every citation attached to the answer refers to a manually expected passage.",
        },
        "summary": summary,
        "cases": [asdict(result) for result in results],
    }


def write_results(output_path: Path = DEFAULT_OUTPUT_PATH) -> dict[str, Any]:
    """Run the experiment and persist its measurements."""

    result = run_experiment()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    report = write_results()
    for limit, metrics in report["summary"].items():
        print(
            f"limit={limit} "
            f"answer_correct={metrics['answer_correct_rate']:.3f} "
            f"irrelevant={metrics['average_irrelevant_passages']:.3f} "
            f"citation_correct={metrics['citation_correct_rate']:.3f}"
        )
