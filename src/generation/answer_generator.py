from typing import Optional, Tuple
from src.core.types import Article, Citation


class AnswerGenerator:
    """
    Given retrieved articles, generate an answer with citations.
    """

    def generate(self, query: str, articles: list[Article]) -> Tuple[Optional[str], bool, Optional[str]]:
        """
        Given a question and relevant articles, produce an answer.
        
        Returns: (answer_text, should_refuse, refusal_reason)
        """
        if not articles:
            return None, True, "No relevant articles found"

        # For now i just concatenate the articles as a simple answer
        # if it was on production i would use an LLM here
        answer = f"Based on the retrieved articles:\n\n"
        for article in articles:
            answer += f"Article {article.article_number} ({article.law_id}):\n"
            answer += article.text + "\n\n"
        
        return answer, False, None


    def ground_citations(self, answer:str, articles:list[Article]) -> list[Citation]:
        """
        Extract citations from the answer and match them to articles.
        """

        citations = []

        for article in articles:
            if f"Article {article.article_number}" in answer:
                # Simple heuristic: if article number appears in answer, cite it
                citations.append(Citation(
                    law_id=article.law_id,
                    article=article.article_number,
                    page=article.page_number,
                    quote=article.text[:100],  # First 100 chars
                    is_verbatim=True,
                ))
        return citations
