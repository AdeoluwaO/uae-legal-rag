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
    
    def add_article(self, article: Article):
        """Store one article"""
        self.articles.append(article)
    
    def add_articles(self, articles: List[Article]):
         """Store multiple articles"""
         self.articles.extend(articles)
    
    def get_articles_by_law (self, law_id: str) -> List[Article]:
         """Get all articles from one law"""
         return [a for a in self.articles if a.law_id == law_id]

    def get_article(self, law_id: str, article_number: str) -> Optional[Article]:
        """Get a specific article by ID and number"""
        for a in self.articles:
            if a.law_id == law_id and a.article_number == article_number:
                return a
        return None


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
            }
            for a in self.articles
        ]

        full_path = os.path.join(self.__folder, filepath)

        with open(full_path, 'w') as f:
            json.dump(data, f, indent=2)
    
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
                    page_number=item["page_number"]
                )
                self.add_article(article)