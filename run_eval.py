from src.core.manifest_loader import load_manifest
from src.retrieval.document_retriever import DocumentRetriever
from src.storage.structured_store import ArticleStorage
from src.generation.answer_generator import AnswerGenerator
from src.evaluation.evaluator import Evaluator

class SimpleQueryEngine:
    def answer(self, query):
        from src.core.types import QueryResult
        from datetime import datetime
        import time
        
        start = time.time()
        docs = load_manifest('input_corpus/baseline.yaml')
        picker = DocumentRetriever(docs)
        selected_docs, refusal = picker.pick_for_query(query)
        
        if refusal:
            return QueryResult(
                query=query, answer=None, citations=[], 
                documents_considered=[d.law_id for d in docs],
                documents_used=[], refused=True, 
                refusal_reason=refusal, timestamp=datetime.now().isoformat(),
                latency_ms=(time.time()-start)*1000
            )
        
        storage = ArticleStorage()
        storage.load_from_json('articles_index.json')
        
        by_law = []
        for doc in selected_docs:
            by_law.extend(storage.get_articles_by_law(doc.law_id))
        
        generator = AnswerGenerator()
        answer, refused, refusal_reason = generator.generate(query, by_law)
        citations = generator.ground_citations(answer, by_law) if answer else []
        
        return QueryResult(
            query=query, answer=answer, citations=citations,
            documents_considered=[d.law_id for d in docs],
            documents_used=[d.law_id for d in selected_docs],
            refused=refused, refusal_reason=refusal_reason,
            timestamp=datetime.now().isoformat(),
            latency_ms=(time.time()-start)*1000
        )

evaluator = Evaluator('eval/golden_set.jsonl')
evaluator.load_golden_set()
results = evaluator.run_golden_set(SimpleQueryEngine())
evaluator.save_results()