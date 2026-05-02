import sys
from src.core.manifest_loader import load_manifest
from src.ingestion.parser import extract_text_from_pdf, find_articles
from src.storage.structured_store import ArticleStorage
from src.core.types import Article
from src.retrieval.document_retriever import DocumentRetriever
from src.generation.answer_generator import AnswerGenerator


# def ingest():
#     """
#     Pipeline: Load manifest → Extract all articles from all PDFs → Store
#     """

#     print("Loading manifest...")

#     docs = load_manifest('input_corpus/baseline.yaml')

#     storage = ArticleStorage()
    
#     print(f"Found {len(docs)} documents in manifest")

#     for doc in docs[:1]:  # process the first one only 
#         print(f"\nProcessing {doc.law_id}...")
#         pdf_path = f"input_corpus/data/{doc.filename}"



def ingest():
    """
    Pipeline: Load manifest → Extract all articles from all PDFs → Store
    """
    print("Loading manifest...")
    docs = load_manifest("input_corpus/baseline.yaml")
    
    storage = ArticleStorage()
    
    print(f"Found {len(docs)} documents in manifest")
    
    for doc in docs[:1]:  # For now, just process the first one
        print(f"\nProcessing {doc.law_id}...")
        pdf_path = f"input_corpus/data/{doc.filename}"
        
        try:
            text = extract_text_from_pdf(pdf_path)
            print(f"  Extracted {len(text)} characters")
            
            articles_found = find_articles(text, doc.law_id)
            print(f"  Found {len(articles_found)} articles")
            
            for article_num, _, _, article_text in articles_found:
                article = Article(
                    law_id=doc.law_id,
                    article_number=article_num,
                    text=article_text,
                    page_number=0,  # We could extract this more carefully
                )
                storage.add_article(article)
        
        except Exception as e:
            print(f"  Error: {e}")
    
    storage.save_to_json("articles_index.json")
    print(f"\nIndexed {len(storage.articles)} total articles")
    print("Saved to articles_index.json")

def ask(query: str):
    """
    Pipeline: Load documents → Pick right ones → Get articles → Generate answer
    """
    print(f"Question: {query}\n")
    
    # Load manifest
    docs = load_manifest("input_corpus/baseline.yaml")
    
    # Pick the right documents
    picker = DocumentRetriever(docs)
    selected_docs, refusal = picker.pick_for_query(query)
    
    if refusal:
        print(f"❌ Cannot answer: {refusal}")
        return
    
    print(f"Selected documents: {[d.law_id for d in selected_docs]}\n")
    
    # Load articles from storage
    storage = ArticleStorage()
    storage.load_from_json("articles_index.json")
    
    # Get articles from selected documents
    relevant_articles = []
    for doc in selected_docs:
        relevant_articles.extend(storage.get_articles_by_law(doc.law_id))
    
    print(f"Found {len(relevant_articles)} relevant articles\n")
    
    # Generate answer
    generator = AnswerGenerator()
    answer, refused, refusal_reason = generator.generate(query, relevant_articles)
    
    if refused:
        print(f"❌ Refused: {refusal_reason}")
    else:
        print("✅ Answer:")
        print(answer)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "ask":
        query = " ".join(sys.argv[2:])
        ask(query)
    else:
        ingest()
