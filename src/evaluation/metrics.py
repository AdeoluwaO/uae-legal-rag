"""
Metrics calculation for evaluation.

Implements: recall@k, quotation fidelity, latency breakdown
"""

from typing import List, Dict, Any


class MetricsCalculator:
    """Calculate evaluation metrics from query results"""

    @staticmethod
    def recall_at_k(results: List[Dict[str, Any]], k: int = 5) -> float:
        """
        Calculate recall@k for document retrieval.

        Recall = (# queries where expected article was in top k) / (# non-refused queries)

        Args:
            results: List of evaluation result dicts
            k: Top-k parameter

        Returns:
            Recall@k as a float between 0 and 1
        """
        non_refused = [r for r in results if not r.get("expected", {}).get("expected_refusal")]

        if not non_refused:
            return 0.0

        correct = 0
        for result in non_refused:
            expected_citations = result.get("expected", {}).get("expected_citations", [])
            actual = result.get("actual", {})
            actual_citations = actual.get("citations", [])

            # Check if any expected citation appears in actual
            for exp_citation in expected_citations:
                exp_law_id = exp_citation.get("law_id")
                if any(c.get("law_id") == exp_law_id for c in actual_citations[:k]):
                    correct += 1
                    break

        return round(correct / len(non_refused), 2)

    @staticmethod
    def quotation_fidelity(results: List[Dict[str, Any]]) -> float:
        """
        Measure quotation fidelity: % of quotes that are verbatim.

        Fidelity = (# verbatim citations) / (# total citations)
        """
        total_citations = 0
        verbatim_citations = 0

        for result in results:
            actual = result.get("actual", {})
            citations = actual.get("citations", [])

            for citation in citations:
                total_citations += 1
                if citation.get("is_verbatim", False):
                    verbatim_citations += 1

        if total_citations == 0:
            return 0.0

        return round(verbatim_citations / total_citations, 2)

    @staticmethod
    def accuracy(results: List[Dict[str, Any]]) -> float:
        """
        Calculate end-to-end accuracy.

        Accuracy = # correct answers / # total queries

        A query is correct if:
        - Refusal status matches expected
        - If not refused, contains expected citations
        """
        correct = 0

        for result in results:
            if result.get("passed", False):
                correct += 1

        return round(correct / len(results), 2) if results else 0.0

    @staticmethod
    def latency_breakdown(results: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate latency statistics across queries.

        Returns p50 and p95 latencies
        """
        latencies = []

        for result in results:
            actual = result.get("actual", {})
            if isinstance(actual, dict) and "latency_ms" in actual:
                latencies.append(actual["latency_ms"])

        if not latencies:
            return {"p50_ms": 0, "p95_ms": 0, "avg_ms": 0}

        latencies.sort()
        n = len(latencies)

        p50 = latencies[int(n * 0.5)]
        p95 = latencies[int(n * 0.95)]
        avg = sum(latencies) / n

        return {
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "avg_ms": round(avg, 2),
            "min_ms": round(min(latencies), 2),
            "max_ms": round(max(latencies), 2)
        }

    @staticmethod
    def refusal_accuracy(results: List[Dict[str, Any]]) -> float:
        """
        Accuracy specifically for refusal cases.

        Refusal = (# correct refusals) / (# expected refusals)
        """
        expected_refusals = [r for r in results if r.get("expected", {}).get("expected_refusal")]

        if not expected_refusals:
            return 0.0

        correct = sum(1 for r in expected_refusals if r.get("passed", False))

        return round(correct / len(expected_refusals), 2)

    @staticmethod
    def generate_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive metrics report.

        Returns dict with all metrics
        """
        report = {
            "metrics": {
                "accuracy": MetricsCalculator.accuracy(results),
                "recall@5": MetricsCalculator.recall_at_k(results, k=5),
                "quotation_fidelity": MetricsCalculator.quotation_fidelity(results),
                "refusal_accuracy": MetricsCalculator.refusal_accuracy(results),
                "latency": MetricsCalculator.latency_breakdown(results)
            }
        }

        # Failure mode analysis
        failures = [r for r in results if not r.get("passed", False)]
        report["failure_count"] = len(failures)
        report["failure_modes"] = {
            "wrong_jurisdiction": sum(1 for r in failures if "jurisdiction" in r.get("expected", {}).get("expected_refusal_reason", "")),
            "repealed_law": sum(1 for r in failures if "repealed" in r.get("expected", {}).get("expected_refusal_reason", "")),
            "missing_citation": sum(1 for r in failures if not r.get("expected", {}).get("expected_refusal")),
            "refused_incorrectly": sum(1 for r in failures if r.get("actual", {}).get("refused"))
        }

        return report
