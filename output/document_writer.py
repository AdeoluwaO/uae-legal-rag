import json
import os
from datetime import datetime
from typing import List
from src.core.types import QueryResult

class DocumentWriter:
    """Save query results to files"""
    
    def __init__(self, output_dir: str = "eval/results"):
        self.output_dir = output_dir
        
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def save_query_result(self, result: QueryResult) -> str:
        """
        Save one Q&A result to a JSON file.
        
        Returns: Path to the file created
        """
        # Generate filename: answer_2026_05_02_143022.json
        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        filename = f"answer_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        # Write to file
        with open(filepath, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        return filepath
    
    def save_all_results(self, results: List[QueryResult]):
        """
        Save all results and create a summary.
        """
        # Save each result
        for result in results:
            self.save_query_result(result)
        
        # Create summary file
        self._create_summary(results)
    
    def _create_summary(self, results: List[QueryResult]):
        """
        Create eval/results/summary.json with aggregate stats.
        """
        total = len(results)
        answered = sum(1 for r in results if not r.refused)
        refused = total - answered
        
        avg_latency = sum(r.latency_ms for r in results) / total if total > 0 else 0
        
        # Count citations per answer
        citations_count = sum(
            len(r.citations) for r in results if not r.refused
        )
        citations_per_answer = citations_count / answered if answered > 0 else 0
        
        summary = {
            "generation_timestamp": datetime.now().isoformat(),
            "total_queries": total,
            "answered": answered,
            "refused": refused,
            "answer_rate_percent": round((answered / total * 100) if total > 0 else 0, 1),
            "average_latency_ms": round(avg_latency, 2),
            "average_citations_per_answer": round(citations_per_answer, 2),
        }
        
        filepath = os.path.join(self.output_dir, "summary.json")
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nSummary saved to {filepath}")
