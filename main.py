import time
import json
import os
from datetime import datetime
from src.core.types import QueryResult
from output.document_writer import DocumentWriter
import sys
from src.core.manifest_loader import load_manifest
from src.ingestion.parser import extract_text_from_pdf, find_articles
from src.storage.structured_store import ArticleStorage
from src.core.types import Article
from src.retrieval.document_retriever import DocumentRetriever
from src.generation.answer_generator import AnswerGenerator


def ingest():
    """
    Pipeline: Load manifest  Extract all articles from all PDFs Store
    """
    print("Loading manifest...")
    docs = load_manifest("input_corpus/baseline.yaml")

    storage = ArticleStorage()
    ingest_start = time.time()

    print(f"Found {len(docs)} documents in manifest")

    # Track status of each document
    doc_status = []

    for doc in docs:
        print(f"\nProcessing {doc.law_id}...")
        pdf_path = f"input_corpus/data/{doc.filename}"

        status_entry = {
            "law_id": doc.law_id,
            "filename": doc.filename,
            "status": "ok",
            "articles_detected": 0,
            "chunks_produced": 0,
            "embed_time_ms": 0,
            "parse_time_ms": 0,
            "errors": []
        }

        try:
            parse_start = time.time()
            text = extract_text_from_pdf(pdf_path)
            print(f"  Extracted {len(text)} characters")
            status_entry["parse_time_ms"] = round((time.time() - parse_start) * 1000, 2)

            articles_found = find_articles(text, doc.law_id)
            print(f"  Found {len(articles_found)} articles")
            status_entry["articles_detected"] = len(articles_found)

            embed_start = time.time()
            for article_num, _, _, article_text in articles_found:
                article = Article(
                    law_id=doc.law_id,
                    article_number=article_num,
                    text=article_text,
                    page_number=0,
                )
                storage.add_article(article)
                status_entry["chunks_produced"] += 1

            status_entry["embed_time_ms"] = round((time.time() - embed_start) * 1000, 2)

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"  Error: {error_msg}")
            status_entry["status"] = "error"
            status_entry["errors"].append(error_msg)

        doc_status.append(status_entry)

    # Save index
    storage.save_to_json("articles_index.json")
    total_time = time.time() - ingest_start

    print(f"\n Indexing complete!")
    print(f"  Total articles: {len(storage.articles)}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Saved to generated_data/articles_index.json")

    # Create ingestion artifact
    os.makedirs("eval/results", exist_ok=True)
    ingestion_artifact = {
        "corpus_date": datetime.now().isoformat(),
        "total_documents": len(docs),
        "total_time_seconds": round(total_time, 2),
        "documents": doc_status,
        "summary": {
            "total_articles": len(storage.articles),
            "total_index_size_mb": round(os.path.getsize("generated_data/articles_index.json") / (1024*1024), 2)
        }
    }

    with open("eval/results/indexing.json", "w") as f:
        json.dump(ingestion_artifact, f, indent=2)

    print(f"  Ingestion artifact: eval/results/indexing.json")

def ask(query: str):
    """Answer a question and save result to file"""
    start_time = time.time()
    
    print(f"Question: {query}\n")
    
    # Load manifest
    docs = load_manifest("input_corpus/baseline.yaml")
    
    # Pick the right documents
    picker = DocumentRetriever(docs)
    selected_docs, refusal = picker.pick_for_query(query)
    
    documents_considered = [d.law_id for d in docs]
    documents_used = [d.law_id for d in selected_docs] if selected_docs else []
    
    if refusal:
        # Create refusal result
        latency_ms = (time.time() - start_time) * 1000
        result = QueryResult(
            query=query,
            answer=None,
            citations=[],
            documents_considered=documents_considered,
            documents_used=[],
            refused=True,
            refusal_reason=refusal,
            timestamp=datetime.now().isoformat(),
            latency_ms=latency_ms,
        )
        
        # Save to file
        writer = DocumentWriter()
        filepath = writer.save_query_result(result)
        print(f"Cannot answer: {refusal}")
        print(f"Result saved to: {filepath}\n")
        return
    
    print(f"Selected documents: {documents_used}\n")
    
    # Load articles from storage
    storage = ArticleStorage()
    storage.load_from_json("articles_index.json")
    
    # Get relevant articles (structured + vector)
    print("Searching articles...")
    by_law = []
    for doc in selected_docs:
        by_law.extend(storage.get_articles_by_law(doc.law_id))
    
    by_similarity = storage.search_by_similarity(query, top_k=5)
    
    # Combine
    seen = set()
    relevant_articles = []
    for article in by_law:
        key = (article.law_id, article.article_number)
        if key not in seen:
            relevant_articles.append(article)
            seen.add(key)
    
    for article, score in by_similarity:
        key = (article.law_id, article.article_number)
        if key not in seen:
            relevant_articles.append(article)
            seen.add(key)
    
    print(f"Found {len(relevant_articles)} articles\n")
    
    # Generate answer
    generator = AnswerGenerator()
    answer, refused_gen, refusal_reason_gen = generator.generate(
        query, relevant_articles
    )
    
    # Ground citations
    citations = generator.ground_citations(answer, relevant_articles) if answer else []
    
    # Calculate latency
    latency_ms = (time.time() - start_time) * 1000
    
    # Create result
    result = QueryResult(
        query=query,
        answer=answer,
        citations=citations,
        documents_considered=documents_considered,
        documents_used=documents_used,
        refused=refused_gen,
        refusal_reason=refusal_reason_gen,
        timestamp=datetime.now().isoformat(),
        latency_ms=latency_ms,
    )
    
    # Save to file
    writer = DocumentWriter()
    filepath = writer.save_query_result(result)
    
    # Print
    if refused_gen:
        print(f"Refused: {refusal_reason_gen}")
    else:
        print("Answer:")
        print(answer)
        print(f"\nCitations: {len(citations)}")
        for cit in citations:
            print(f"  - {cit.law_id}, Article {cit.article}")
    
    print(f"Result saved to: {filepath}")
    print(f"Latency: {latency_ms:.2f}ms\n")
    

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "ask":
        query = " ".join(sys.argv[2:])
        ask(query)
    else:
        ingest()


