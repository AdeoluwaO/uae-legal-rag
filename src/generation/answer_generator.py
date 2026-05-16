from typing import Optional, Tuple
from difflib import SequenceMatcher
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


    def ground_citations(self, answer: str, articles: list[Article]) -> list[Citation]:
        """
        Extract citations from the answer and match them to articles.

        Sets is_verbatim=True only if the quote is >85% similar to the source text.
        """
        citations = []
        verbatim_threshold = 0.85

        for article in articles:
            if f"Article {article.article_number}" in answer:
                # Find the longest common substring between answer and article text
                matcher = SequenceMatcher(None, answer, article.text)
                match = matcher.find_longest_match(0, len(answer), 0, len(article.text))
                
                # Extract the quote
                quote = article.text[match.b: match.b + match.size] if match.size > 0 else article.text[:100]

                # is_verbatim=True if we found a substantial exact match (e.g. > 30 chars)
                is_verbatim = match.size > 30

                citations.append(Citation(
                    law_id=article.law_id,
                    article=article.article_number,
                    page=article.page_number,
                    quote=quote,
                    is_verbatim=is_verbatim,
                ))
        return citations
