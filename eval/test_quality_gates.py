"""Quality gate tests for the RAG evaluation pipeline.

These tests run the full evaluation pipeline against the golden dataset
and assert minimum quality thresholds. They are designed to run in CI
to prevent quality regressions.
"""

import pytest
from eval.evaluator import RAGEvaluator

# Quality thresholds — failing any of these breaks the build
ANSWER_RELEVANCE_THRESHOLD = 0.75
CITATION_PRECISION_THRESHOLD = 0.70
CITATION_RECALL_THRESHOLD = 0.60
ABSTENTION_ACCURACY_THRESHOLD = 0.80

# Performance/Operational thresholds
P50_LATENCY_THRESHOLD = 4.0
P95_LATENCY_THRESHOLD = 8.0
COST_PER_REQUEST_THRESHOLD = 0.01
FAILURE_RATE_THRESHOLD = 0.10


@pytest.fixture(scope="module")
def eval_report():
    """Run the evaluation once and share across all tests."""
    evaluator = RAGEvaluator()
    report = evaluator.run()
    evaluator.save_report(report)
    return report


class TestQualityGates:
    """Quality gate assertions for the RAG pipeline."""

    def test_answer_relevance(self, eval_report):
        """Answer relevance must meet the minimum threshold."""
        assert eval_report.avg_answer_relevance >= ANSWER_RELEVANCE_THRESHOLD, (
            f"Answer relevance {eval_report.avg_answer_relevance:.4f} "
            f"< threshold {ANSWER_RELEVANCE_THRESHOLD}"
        )

    def test_citation_precision(self, eval_report):
        """Citation precision must meet the minimum threshold."""
        assert eval_report.avg_citation_precision >= CITATION_PRECISION_THRESHOLD, (
            f"Citation precision {eval_report.avg_citation_precision:.4f} "
            f"< threshold {CITATION_PRECISION_THRESHOLD}"
        )

    def test_citation_recall(self, eval_report):
        """Citation recall must meet the minimum threshold."""
        assert eval_report.avg_citation_recall >= CITATION_RECALL_THRESHOLD, (
            f"Citation recall {eval_report.avg_citation_recall:.4f} "
            f"< threshold {CITATION_RECALL_THRESHOLD}"
        )

    def test_abstention_accuracy(self, eval_report):
        """Abstention accuracy must meet the minimum threshold."""
        assert eval_report.abstention_accuracy >= ABSTENTION_ACCURACY_THRESHOLD, (
            f"Abstention accuracy {eval_report.abstention_accuracy:.4f} "
            f"< threshold {ABSTENTION_ACCURACY_THRESHOLD}"
        )

    def test_p50_latency(self, eval_report):
        """P50 Latency must be below the maximum threshold."""
        assert eval_report.p50_latency <= P50_LATENCY_THRESHOLD, (
            f"P50 Latency {eval_report.p50_latency:.4f}s "
            f"> threshold {P50_LATENCY_THRESHOLD}s"
        )

    def test_p95_latency(self, eval_report):
        """P95 Latency must be below the maximum threshold."""
        assert eval_report.p95_latency <= P95_LATENCY_THRESHOLD, (
            f"P95 Latency {eval_report.p95_latency:.4f}s "
            f"> threshold {P95_LATENCY_THRESHOLD}s"
        )

    def test_cost_per_request(self, eval_report):
        """Average cost per request must be below the maximum threshold."""
        assert eval_report.avg_cost <= COST_PER_REQUEST_THRESHOLD, (
            f"Average cost ${eval_report.avg_cost:.6f} "
            f"> threshold ${COST_PER_REQUEST_THRESHOLD}"
        )

    def test_failure_rate(self, eval_report):
        """Failure rate must be below the maximum threshold."""
        assert eval_report.failure_rate <= FAILURE_RATE_THRESHOLD, (
            f"Failure rate {eval_report.failure_rate:.4f} "
            f"> threshold {FAILURE_RATE_THRESHOLD}"
        )

    def test_no_empty_results(self, eval_report):
        """Ensure the evaluation actually ran on questions."""
        assert eval_report.total_questions > 0, "No evaluation results found"
        assert eval_report.answerable_questions > 0, "No answerable questions evaluated"
        assert eval_report.unanswerable_questions > 0, "No unanswerable questions evaluated"

    def test_report_saved(self, eval_report):
        """Ensure the evaluation report was saved."""
        from pathlib import Path
        assert Path("eval/reports/latest.json").exists(), "Evaluation report not saved"
