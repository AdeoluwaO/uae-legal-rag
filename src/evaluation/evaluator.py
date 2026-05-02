import json
import os
from typing import List, Dict, Any
from src.core.types import QueryResult


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

        Simple check:
        - Refusal status matches
        - If not refused, contains expected law_ids in citations
        """
        if expected["expected_refusal"]:
            return actual.refused
        else:
            if actual.refused:
                return False

            # Check if expected citations appear in result
            if not expected.get("expected_citations"):
                return True

            for exp_citation in expected["expected_citations"]:
                law_id = exp_citation.get("law_id")
                if law_id and not any(c.law_id == law_id for c in actual.citations):
                    return False

            return True

    def save_results(self):
        """Save evaluation results to JSON"""
        os.makedirs(self.output_dir, exist_ok=True)

        # Save detailed results
        results_file = os.path.join(self.output_dir, "traces.jsonl")
        with open(results_file, 'w') as f:
            for result in self.results:
                f.write(json.dumps(result) + "\n")

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
            "evaluated_date": __import__('datetime').datetime.now().isoformat()
        }

        summary_file = os.path.join(self.output_dir, "summary.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\n Evaluation Complete:")
        print(f"  Total: {total}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {total - passed}")
        print(f"  Pass Rate: {summary['pass_rate']}%")
        print(f"\n Results saved to:")
        print(f"  - {results_file}")
        print(f"  - {summary_file}")

        return summary
