from embedding.embedding.embedder import EmbeddingEngine
import os
import json
from typing import List, Optional
from src.core.types import Article, Document


class ArticleStorage:
    """
    Simple in-memory storage for articles.
    """

    __folder = "generated_data"

    def __init__(self):
        self.articles: List[Article] = []
        self.embedder = EmbeddingEngine()
    
    def add_article(self, article: Article):
        """Store one article"""
        if article.embedding is None:
            embeddings = self.embedder.embed_batch([article.text])
            if embeddings:
                article.embedding = embeddings[0]

        self.articles.append(article)
    
    def add_articles(self, articles: List[Article]):
         """Store multiple articles"""
         text_to_embed = [ article.text for article in articles if article.embedding is None]

         if text_to_embed: 
            embeddings = self.embedder.embed_batch(text_to_embed)
            
            embedding_idx = 0
            for article in articles:
                if article.embedding is None and embedding_idx < len(embeddings):
                    article.embedding = embeddings[embedding_idx]
                    embedding_idx += 1

         self.articles.extend(articles)
    
    def get_articles_by_law(self, law_id: str) -> List[Article]:
         """Get all articles from one law"""
         return [a for a in self.articles if a.law_id == law_id]

    def remove_articles_by_law(self, law_id: str) -> int:
        """Remove all articles from a specific law. Returns count removed."""
        original_count = len(self.articles)
        self.articles = [a for a in self.articles if a.law_id != law_id]
        return original_count - len(self.articles)

    def get_article(self, law_id: str, article_number: str) -> Optional[Article]:
        """Get a specific article by ID and number"""
        for a in self.articles:
            if a.law_id == law_id and a.article_number == article_number:
                return a
        return None
    
    def search_by_similarity(self, query: str, top_k: int = 5) -> List[tuple[Article, float]]:
        """
        Find articles most similar to a query.

        Returns: List of (Article, similarity_score)

        Highest similarity first
        """

        embeddings_list = self.embedder.embed_batch([query])

        if not embeddings_list:
            print("Error embedding query")
            return []

        query_embedding = embeddings_list[0]

        # Calculate similarity between query and all articles
        similarities = []

        for article in self.articles:
            if article.embedding is None:
                continue

            similarity = self.embedder.calculate_similarity(query_embedding, article.embedding)
            similarities.append((article, similarity))

        # Sort by highest similarity first 
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top k 
        return similarities[:top_k]

    def save_to_json(self, filepath: str):
        """Save all articles to a JSON file for later"""

        if not os.path.exists(self.__folder):
            os.makedirs(self.__folder)

        data = [
            {
                "law_id": a.law_id,
                "article_number": a.article_number,
                "text": a.text,
                "page_number": a.page_number,
                "embedding": a.embedding,
            }
            for a in self.articles
        ]

        full_path = os.path.join(self.__folder, filepath)

        with open(full_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(data)} articles to {filepath}")

    def load_from_json(self, filepath: str):
        """Load articles from a JSON file"""

        full_path = os.path.join(self.__folder, filepath)

        with open(full_path, 'r') as f:
            data = json.load(f)

            for item in data:
                article = Article(
                    law_id=item["law_id"],
                    article_number=item["article_number"],
                    text=item["text"],
                    page_number=item["page_number"],
                    embedding=item["embedding"]
                )
                self.add_article(article)
            
        print(f"Loaded {len(self.articles)} articles from {filepath}")