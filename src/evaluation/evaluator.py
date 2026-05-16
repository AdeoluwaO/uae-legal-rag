import json
import os
from typing import List, Dict, Any
from src.core.types import QueryResult
from src.evaluation.metrics import MetricsCalculator


class Evaluator:
    """Run evaluation against golden set"""

    def __init__(self, golden_set_path: str, output_dir: str = "eval/results"):
        self.golden_set_path = golden_set_path
        self.output_dir = output_dir
        self.golden_set = []
        self.results = []

    def load_golden_set(self):
        """Load golden set from JSONL file"""
        with open(self.golden_set_path, 'r') as f:
            for line in f:
                if line.strip():
                    self.golden_set.append(json.loads(line))
        print(f"Loaded {len(self.golden_set)} test cases from golden set")

    def run_golden_set(self, query_engine) -> List[Dict[str, Any]]:
        """
        Run all golden set queries through the system.

        Args:
            query_engine: QueryEngine instance with ask() method

        Returns:
            List of results with expected vs actual answers
        """
        if not self.golden_set:
            self.load_golden_set()

        print(f"\nRunning {len(self.golden_set)} test cases...\n")

        for i, test_case in enumerate(self.golden_set, 1):
            query = test_case["query"]
            expected = test_case

            print(f"[{i}/{len(self.golden_set)}] {query[:60]}...")

            try:
                # Run query through system
                result = query_engine.answer(query)

                # Compare with expected
                comparison = {
                    "query": query,
                    "expected": expected,
                    "actual": result.to_dict() if hasattr(result, 'to_dict') else result,
                    "passed": self._check_correctness(expected, result)
                }
                self.results.append(comparison)
            except Exception as e:
                print(f" Error: {e}")
                self.results.append({
                    "query": query,
                    "expected": expected,
                    "error": str(e),
                    "passed": False
                })

        return self.results

    def _check_correctness(self, expected: Dict, actual: QueryResult) -> bool:
        """
        Check if actual result matches expected result.

        Rules:
        - If expected_refusal=True: actual must be refused
        - If expected_refusal=False: actual must not be refused AND contain expected citations
        """
        expected_should_refuse = expected.get("expected_refusal", False)

        # If we expect a refusal, check that it actually refused
        if expected_should_refuse:
            if not actual.refused:
                return False
            # Check if the refusal reason is conceptually correct
            expected_reason = expected.get("expected_refusal_reason", "").lower()
            actual_reason = (actual.refusal_reason or "").lower()
            
            # Simple check to see if key elements of the expected reason are in the actual reason
            if "jurisdiction" in expected_reason and "jurisdiction" not in actual_reason and "difc" not in actual_reason:
                return False
            if "repealed" in expected_reason and "repealed" not in actual_reason and "current laws" not in actual_reason:
                return False
                
            return True

        # If we don't expect a refusal, it must not refuse
        if actual.refused:
            return False

        # For non-refused cases, check that expected citations appear in result
        expected_citations = expected.get("expected_citations", [])
        if not expected_citations:
            # No expected citations → just need a non-refusal answer
            return True

        # Verify at least one expected citation is present
        for exp_citation in expected_citations:
            law_id = exp_citation.get("law_id")
            if law_id and any(c.law_id == law_id for c in actual.citations):
                return True

        # No expected citations found
        return False

    def save_results(self):
        """Save evaluation results to JSON with comprehensive metrics"""
        os.makedirs(self.output_dir, exist_ok=True)

        # Save detailed results
        results_file = os.path.join(self.output_dir, "traces.jsonl")
        with open(results_file, 'w') as f:
            for result in self.results:
                f.write(json.dumps(result) + "\n")

        # Generate comprehensive metrics report
        metrics_report = MetricsCalculator.generate_report(self.results)

        # Calculate summary stats
        total = len(self.results)
        passed = sum(1 for r in self.results if r.get("passed", False))
        refused_count = sum(1 for r in self.results if r.get("actual", {}).get("refused", False))

        summary = {
            "total_queries": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(passed / total * 100, 1) if total > 0 else 0,
            "refused_queries": refused_count,
            "metrics": metrics_report.get("metrics", {}),
            "failure_analysis": {
                "total_failures": metrics_report.get("failure_count", 0),
                "failure_modes": metrics_report.get("failure_modes", {})
            },
            "evaluated_date": __import__('datetime').datetime.now().isoformat()
        }

        summary_file = os.path.join(self.output_dir, "summary.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        # Print detailed report
        print(f"\n Evaluation Complete:")
        print(f"  Total Queries: {total}")
        print(f"  Passed: {passed} ({summary['pass_rate']}%)")
        print(f"  Failed: {total - passed}")
        print(f"\n Metrics:")
        metrics = summary.get("metrics", {})
        print(f"  Accuracy: {metrics.get('accuracy', 0)}")
        print(f"  Recall@5: {metrics.get('recall@5', 0)}")
        print(f"  Quotation Fidelity: {metrics.get('quotation_fidelity', 0)}")
        print(f"  Refusal Accuracy: {metrics.get('refusal_accuracy', 0)}")
        latency = metrics.get('latency', {})
        print(f"  Latency (avg): {latency.get('avg_ms', 0):.1f}ms")
        print(f"\n Results saved to:")
        print(f"  - {results_file}")
        print(f"  - {summary_file}")

        return summary
