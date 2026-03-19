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

    def test_no_empty_results(self, eval_report):
        """Ensure the evaluation actually ran on questions."""
        assert eval_report.total_questions > 0, "No evaluation results found"
        assert eval_report.answerable_questions > 0, "No answerable questions evaluated"
        assert eval_report.unanswerable_questions > 0, "No unanswerable questions evaluated"

    def test_report_saved(self, eval_report):
        """Ensure the evaluation report was saved."""
        from pathlib import Path
        assert Path("eval/reports/latest.json").exists(), "Evaluation report not saved"
