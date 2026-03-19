"""RAG evaluation pipeline with multiple metrics."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from groq import Groq

from src.config import settings
from src.generation.generator import RAGGenerator


@dataclass
class EvalResult:
    """Result for a single evaluation question."""
    question_id: int
    question: str
    category: str
    expected_answer: str
    expected_sources: list[str]
    actual_answer: str
    actual_sources: list[str]
    is_declined: bool
    answer_relevance: float = 0.0
    citation_precision: float = 0.0
    citation_recall: float = 0.0
    abstention_correct: bool = False
    latency: float = 0.0
    cost: float = 0.0


@dataclass
class EvalReport:
    """Aggregate evaluation report."""
    results: list[EvalResult] = field(default_factory=list)
    avg_answer_relevance: float = 0.0
    avg_citation_precision: float = 0.0
    avg_citation_recall: float = 0.0
    abstention_accuracy: float = 0.0
    p50_latency: float = 0.0
    p95_latency: float = 0.0
    avg_cost: float = 0.0
    failure_rate: float = 0.0
    total_questions: int = 0
    answerable_questions: int = 0
    unanswerable_questions: int = 0


class RAGEvaluator:
    """Evaluates RAG pipeline quality against a golden dataset."""

    def __init__(self, dataset_path: str = "eval/golden_dataset.json"):
        self.dataset_path = Path(dataset_path)
        self.generator = RAGGenerator()
        self.client = Groq(api_key=settings.groq_api_key)

    def _load_dataset(self) -> list[dict]:
        """Load the golden evaluation dataset."""
        return json.loads(self.dataset_path.read_text(encoding="utf-8"))

    def _judge_relevance(
        self, question: str, expected: str, actual: str
    ) -> float:
        """Use LLM-as-judge to score answer relevance (0.0 - 1.0)."""
        prompt = f"""You are an evaluation judge. Score how well the actual answer matches the expected answer for the given question.

Question: {question}

Expected Answer: {expected}

Actual Answer: {actual}

Score the actual answer on a scale of 0.0 to 1.0:
- 1.0: The actual answer covers the same key information as the expected answer
- 0.7-0.9: Mostly correct, minor omissions or extra details
- 0.4-0.6: Partially correct, some key information missing or wrong
- 0.1-0.3: Mostly incorrect or irrelevant
- 0.0: Completely wrong or no useful information

Respond with ONLY a number between 0.0 and 1.0, nothing else."""

        try:
            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.0,
            )
            score_str = response.choices[0].message.content.strip()
            score = float(re.search(r"[\d.]+", score_str).group())
            return min(max(score, 0.0), 1.0)
        except Exception:
            return 0.0

    def _compute_citation_precision(
        self, actual_sources: list[str], expected_sources: list[str]
    ) -> float:
        if not actual_sources:
            return 1.0 if not expected_sources else 0.0
        relevant = sum(
            1 for src in actual_sources
            if any(exp in src or src in exp for exp in expected_sources)
        )
        return relevant / len(actual_sources)

    def _compute_citation_recall(
        self, actual_sources: list[str], expected_sources: list[str]
    ) -> float:
        if not expected_sources:
            return 1.0
        found = sum(
            1 for exp in expected_sources
            if any(exp in src or src in exp for src in actual_sources)
        )
        return found / len(expected_sources)

    def evaluate_single(self, item: dict) -> EvalResult:
        """Evaluate a single Q&A pair."""
        question = item["question"]
        expected_answer = item["expected_answer"]
        expected_sources = item.get("expected_sources", [])
        category = item.get("category", "factual")
        is_unanswerable = category == "unanswerable"

        result = self.generator.generate(question)
        actual_sources = [c.source_file for c in result.citations]

        from src.observability.tracer import global_tracer
        global_tracer.log_trace(
            endpoint="/eval",
            question=question,
            answer=result.answer,
            latency=result.latency,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            cost=result.cost,
        )

        eval_result = EvalResult(
            question_id=item["id"],
            question=question,
            category=category,
            expected_answer=expected_answer,
            expected_sources=expected_sources,
            actual_answer=result.answer,
            actual_sources=actual_sources,
            is_declined=result.is_declined,
            latency=result.latency,
            cost=result.cost,
        )

        if is_unanswerable:
            eval_result.abstention_correct = result.is_declined
            eval_result.answer_relevance = 1.0 if result.is_declined else 0.0
            eval_result.citation_precision = 1.0
            eval_result.citation_recall = 1.0
        else:
            if result.is_declined:
                eval_result.answer_relevance = 0.0
                eval_result.citation_precision = 0.0
                eval_result.citation_recall = 0.0
                eval_result.abstention_correct = False
            else:
                eval_result.answer_relevance = self._judge_relevance(
                    question, expected_answer, result.answer
                )
                eval_result.citation_precision = self._compute_citation_precision(
                    actual_sources, expected_sources
                )
                eval_result.citation_recall = self._compute_citation_recall(
                    actual_sources, expected_sources
                )
                eval_result.abstention_correct = True

        return eval_result

    def run(self) -> EvalReport:
        """Run evaluation on the entire golden dataset."""
        dataset = self._load_dataset()
        report = EvalReport(total_questions=len(dataset))

        answerable_relevances = []
        answerable_precisions = []
        answerable_recalls = []
        abstention_results = []

        for item in dataset:
            result = self.evaluate_single(item)
            report.results.append(result)

            if item.get("category") == "unanswerable":
                report.unanswerable_questions += 1
                abstention_results.append(result.abstention_correct)
            else:
                report.answerable_questions += 1
                answerable_relevances.append(result.answer_relevance)
                answerable_precisions.append(result.citation_precision)
                answerable_recalls.append(result.citation_recall)
                abstention_results.append(result.abstention_correct)

        if answerable_relevances:
            report.avg_answer_relevance = sum(answerable_relevances) / len(answerable_relevances)
        if answerable_precisions:
            report.avg_citation_precision = sum(answerable_precisions) / len(answerable_precisions)
        if answerable_recalls:
            report.avg_citation_recall = sum(answerable_recalls) / len(answerable_recalls)
        if abstention_results:
            report.abstention_accuracy = sum(abstention_results) / len(abstention_results)
            
        # Calculate perf metrics
        latencies = sorted([r.latency for r in report.results])
        costs = [r.cost for r in report.results]
        
        if latencies:
            report.p50_latency = latencies[int(len(latencies) * 0.5)]
            report.p95_latency = latencies[int(len(latencies) * 0.95)]
        if costs:
            report.avg_cost = sum(costs) / len(costs)
            
        failures = sum(1 for r in report.results if r.is_declined and r.category != "unanswerable")
        if len(report.results) > 0:
            report.failure_rate = failures / len(report.results)

        return report

    def save_report(self, report: EvalReport, output_path: str = "eval/reports/latest.json") -> None:
        """Save the evaluation report as JSON."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "summary": {
                "total_questions": report.total_questions,
                "answerable_questions": report.answerable_questions,
                "unanswerable_questions": report.unanswerable_questions,
                "avg_answer_relevance": round(report.avg_answer_relevance, 4),
                "avg_citation_precision": round(report.avg_citation_precision, 4),
                "avg_citation_recall": round(report.avg_citation_recall, 4),
                "abstention_accuracy": round(report.abstention_accuracy, 4),
                "p50_latency": round(report.p50_latency, 4),
                "p95_latency": round(report.p95_latency, 4),
                "avg_cost": round(report.avg_cost, 6),
                "failure_rate": round(report.failure_rate, 4),
            },
            "results": [
                {
                    "id": r.question_id,
                    "question": r.question,
                    "category": r.category,
                    "answer_relevance": round(r.answer_relevance, 4),
                    "citation_precision": round(r.citation_precision, 4),
                    "citation_recall": round(r.citation_recall, 4),
                    "abstention_correct": r.abstention_correct,
                    "is_declined": r.is_declined,
                    "latency": round(r.latency, 4),
                    "cost": round(r.cost, 6),
                }
                for r in report.results
            ],
        }

        out.write_text(json.dumps(data, indent=2), encoding="utf-8")
