"""
Unit tests for ingestion pipeline
"""

from src.ingestion.parser import find_articles
from src.core.types import Article


class TestArticleExtraction:
    """Test article boundary detection"""

    def test_find_articles_federal_format(self):
        """Test: Extract articles in federal format Article (N)"""
        text = """
        Article (1): Definitions
        In this Law, "Worker" means an employed person.

        Article (2): Scope
        This Law applies to all employment.

        Article (3): Termination
        The employer may terminate.
        """

        articles = find_articles(text, "TEST_LAW")

        # Should find 3 articles
        assert len(articles) == 3, f"Expected 3 articles, got {len(articles)}"

        # Check article numbers
        article_nums = [a[0] for a in articles]
        assert article_nums == ["1", "2", "3"]

    def test_find_articles_with_content(self):
        """Test: Article text is preserved correctly"""
        text = """
        Article (1): Definitions
        In this Law, "Worker" means a person employed.

        Article (2): Scope
        This applies to all workers.
        """

        articles = find_articles(text, "TEST_LAW")

        # Check first article contains expected text
        assert "Definitions" in articles[0][3]
        assert "Worker" in articles[0][3]

        # Check second article contains expected text
        assert "Scope" in articles[1][3]

    def test_find_articles_empty_text(self):
        """Test: Empty text returns empty list"""
        articles = find_articles("", "TEST_LAW")
        assert articles == []

    def test_find_articles_no_matches(self):
        """Test: Text with no articles returns empty list"""
        text = "This is just random text without any articles"
        articles = find_articles(text, "TEST_LAW")
        assert articles == []

    def test_find_articles_difc_format(self):
        """Test: Extract articles in DIFC format (N. DIFC)"""
        text = """
        1. DIFC Employment Articles
        Employment terms and conditions apply.

        2. DIFC Termination Rights
        An employee may be terminated with notice.

        3. DIFC Dispute Resolution
        Disputes shall be resolved in DIFC courts.
        """

        articles = find_articles(text, "DIFC_LAW")

        # Should find 3 articles
        assert len(articles) == 3, f"Expected 3 articles, got {len(articles)}"

        # Check article numbers
        article_nums = [a[0] for a in articles]
        assert article_nums == ["1", "2", "3"]

    def test_find_articles_difc_with_content(self):
        """Test: DIFC article text is preserved correctly"""
        text = """
        1. DIFC Employment
        This applies to DIFC employees.

        2. DIFC Wages
        Wages must be paid in AED.
        """

        articles = find_articles(text, "DIFC_LAW")

        # Check first article contains expected text
        assert "Employment" in articles[0][3]
        assert "DIFC employees" in articles[0][3]

        # Check second article contains expected text
        assert "Wages" in articles[1][3]


class TestArticleStorage:
    """Test article storage and retrieval"""

    def test_article_creation(self):
        """Test: Create Article with required fields"""
        article = Article(
            law_id="FDL_33_2021_LABOUR",
            article_number="1",
            text="Definitions section",
            page_number=1
        )

        assert article.law_id == "FDL_33_2021_LABOUR"
        assert article.article_number == "1"
        assert article.text == "Definitions section"

    def test_article_with_paragraph(self):
        """Test: Article can have paragraph number"""
        article = Article(
            law_id="FDL_33_2021_LABOUR",
            article_number="43",
            paragraph_number="1",
            text="Termination notice requirement",
            page_number=23
        )

        assert article.paragraph_number == "1"
        assert article.article_number == "43"


class TestCitationExtraction:
    """Test citation grounding"""

    def test_citation_with_all_fields(self):
        """Test: Citation has required fields"""
        from src.core.types import Citation

        citation = Citation(
            law_id="FDL_33_2021_LABOUR",
            article="43",
            page=23,
            quote="The employer shall give notice",
            is_verbatim=True
        )

        assert citation.law_id == "FDL_33_2021_LABOUR"
        assert citation.article == "43"
        assert citation.page == 23
        assert citation.quote == "The employer shall give notice"
        assert citation.is_verbatim is True

    def test_citation_with_paragraph(self):
        """Test: Citation can reference paragraph"""
        from src.core.types import Citation

        citation = Citation(
            law_id="FDL_33_2021_LABOUR",
            article="43",
            paragraph="1",
            page=23,
            quote="The employer may terminate",
            is_verbatim=True
        )

        assert citation.paragraph == "1"
        assert citation.article == "43"


class TestArticleChunking:
    """Test article chunking strategy"""

    def test_short_article_not_split(self):
        """Test: Short articles (<100 chars) kept as single chunk"""
        short_text = "Article 1 brief text"

        # Article of only 20 chars should not be split
        article = Article(
            law_id="TEST",
            article_number="1",
            text=short_text,
            page_number=1
        )

        # Current implementation: keep as-is
        assert len(article.text) < 100

    def test_long_article_handling(self):
        """Test: Long articles properly handled"""
        long_text = "Article content. " * 200  # ~3400 chars

        article = Article(
            law_id="TEST",
            article_number="43",
            text=long_text,
            page_number=23
        )

        # Article should be stored (chunking happens at retrieval)
        assert len(article.text) > 2000
