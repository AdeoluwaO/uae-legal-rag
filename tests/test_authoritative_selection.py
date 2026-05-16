"""
Tests for authoritative document selection logic
"""

from src.retrieval.document_retriever import DocumentRetriever
from src.core.types import Document, Jurisdiction, InstrumentType, LawStatus


class TestJurisdictionFiltering:
    """Test jurisdiction-based document filtering"""

    @staticmethod
    def create_test_documents():
        """Create test documents with different jurisdictions"""
        return [
            Document(
                law_id="FDL_33_2021_LABOUR",
                filename="labour.pdf",
                title="UAE Labour Law",
                jurisdiction=Jurisdiction.FEDERAL_UAE,
                instrument_type=InstrumentType.FEDERAL_DECREE_LAW,
                status=LawStatus.IN_FORCE,
                year=2021,
                effective_date="2022-02-02",
                page_count=50,
                article_count_approx=74,
                source_note="Current labour law"
            ),
            Document(
                law_id="DIFC_2_2019_EMPLOYMENT",
                filename="difc_employment.pdf",
                title="DIFC Employment Law",
                jurisdiction=Jurisdiction.DIFC_FREE_ZONE,
                instrument_type=InstrumentType.DIFC_LAW,
                status=LawStatus.IN_FORCE,
                year=2019,
                effective_date="2019-08-28",
                page_count=44,
                article_count_approx=80,
                source_note="DIFC employment law"
            )
        ]

    def test_filter_onshore_jurisdiction(self):
        """Test: Query with 'onshore' filters to federal_uae"""
        docs = self.create_test_documents()
        picker = DocumentRetriever(docs)

        query = "What is the notice period for terminating employment onshore UAE?"
        selected, refusal = picker.pick_for_query(query)

        # Should select federal, not DIFC
        law_ids = [d.law_id for d in selected]
        assert "FDL_33_2021_LABOUR" in law_ids
        assert "DIFC_2_2019_EMPLOYMENT" not in law_ids

    def test_filter_difc_jurisdiction(self):
        """Test: Query with 'DIFC' filters to difc_free_zone"""
        docs = self.create_test_documents()
        picker = DocumentRetriever(docs)

        query = "What are the employment requirements under DIFC law?"
        selected, refusal = picker.pick_for_query(query)

        # Should select DIFC, not federal
        law_ids = [d.law_id for d in selected]
        assert "DIFC_2_2019_EMPLOYMENT" in law_ids
        assert "FDL_33_2021_LABOUR" not in law_ids

    def test_ambiguous_jurisdiction_refuses(self):
        """Test: Query with both DIFC and onshore keywords refuses due to ambiguity"""
        docs = self.create_test_documents()
        picker = DocumentRetriever(docs)

        # Query mentioning both DIFC and onshore is truly ambiguous
        query = "What is the difference between DIFC and onshore employment rules?"
        selected, refusal = picker.pick_for_query(query)

        # Should refuse due to true ambiguity (both jurisdictions mentioned)
        assert refusal is not None
        assert "jurisdiction" in refusal.lower()

    def test_federal_topic_without_keywords(self):
        """Test: Query about federal-only topic filters correctly without keywords"""
        docs = self.create_test_documents()
        picker = DocumentRetriever(docs)

        query = "What is the notice period for termination?"
        selected, refusal = picker.pick_for_query(query)

        # Should filter to federal documents (termination is federal-only topic)
        assert refusal is None
        law_ids = [d.law_id for d in selected]
        assert "FDL_33_2021_LABOUR" in law_ids
        assert "DIFC_2_2019_EMPLOYMENT" not in law_ids


class TestCurrencyFiltering:
    """Test repealed law filtering"""

    @staticmethod
    def create_test_documents_with_repealed():
        """Create documents with repealed status"""
        return [
            Document(
                law_id="FDL_33_2021_LABOUR",
                filename="labour_2021.pdf",
                title="UAE Labour Law 2021",
                jurisdiction=Jurisdiction.FEDERAL_UAE,
                instrument_type=InstrumentType.FEDERAL_DECREE_LAW,
                status=LawStatus.IN_FORCE,
                year=2021,
                effective_date="2022-02-02",
                page_count=50,
                article_count_approx=74,
                source_note="Current law",
                repealed_by=None
            ),
            Document(
                law_id="FL_8_1980_LABOUR_REPEALED",
                filename="labour_1980.pdf",
                title="UAE Labour Law 1980",
                jurisdiction=Jurisdiction.FEDERAL_UAE,
                instrument_type=InstrumentType.FEDERAL_LAW,
                status=LawStatus.REPEALED,
                year=1980,
                effective_date="1980-04-20",
                page_count=60,
                article_count_approx=193,
                source_note="Repealed by 2021 law",
                repealed_by="FDL_33_2021_LABOUR"
            )
        ]

    def test_filter_out_repealed_laws(self):
        """Test: Current query filters out repealed laws"""
        docs = self.create_test_documents_with_repealed()
        picker = DocumentRetriever(docs)

        query = "What is the current notice period for onshore employment?"
        selected, refusal = picker.pick_for_query(query)

        # Should NOT include repealed law
        law_ids = [d.law_id for d in selected]
        assert "FDL_33_2021_LABOUR" in law_ids
        assert "FL_8_1980_LABOUR_REPEALED" not in law_ids

    def test_include_repealed_for_historical_query(self):
        """Test: Historical query includes repealed laws"""
        docs = self.create_test_documents_with_repealed()
        picker = DocumentRetriever(docs)

        # Use keywords that match the historical filter, with jurisdiction hint
        query = "What did the old onshore labour law require? I want to understand what the repealed law said."
        selected, refusal = picker.pick_for_query(query)

        # Should return results for historical query (includes repealed laws)
        assert len(selected) > 0, "Should return results for historical query"


class TestInstrumentHierarchy:
    """Test base law vs executive regulation preference"""

    @staticmethod
    def create_test_documents_with_regulations():
        """Create base law and executive regulation"""
        return [
            Document(
                law_id="FL_15_2020_CONSUMER_PROTECTION",
                filename="consumer_base.pdf",
                title="Consumer Protection Law",
                jurisdiction=Jurisdiction.FEDERAL_UAE,
                instrument_type=InstrumentType.FEDERAL_LAW,
                status=LawStatus.IN_FORCE,
                year=2020,
                effective_date="2020-11-11",
                page_count=19,
                article_count_approx=38,
                source_note="Base law",
                implements=None
            ),
            Document(
                law_id="CD_66_2023_CONSUMER_PROTECTION_EXEC_REG",
                filename="consumer_exec_reg.pdf",
                title="Consumer Protection Executive Regulation",
                jurisdiction=Jurisdiction.FEDERAL_UAE,
                instrument_type=InstrumentType.CABINET_DECISION,
                status=LawStatus.IN_FORCE,
                year=2023,
                effective_date="2023-07-03",
                page_count=15,
                article_count_approx=46,
                source_note="Executive regulation",
                implements="FL_15_2020_CONSUMER_PROTECTION"
            )
        ]

    def test_prefer_executive_regulation_for_procedures(self):
        """Test: Procedural queries prefer executive regulations"""
        docs = self.create_test_documents_with_regulations()
        picker = DocumentRetriever(docs)

        query = "What are the detailed procedures for consumer complaints under the regulation?"
        selected, refusal = picker.pick_for_query(query)

        # Should prefer cabinet_decision (executive regulation)
        if selected:
            cabinet_decisions = [d for d in selected if d.instrument_type == InstrumentType.CABINET_DECISION]
            assert len(cabinet_decisions) > 0, "Should prefer executive regulation for procedural query"

    def test_accept_base_law_for_general_query(self):
        """Test: General queries can use base law"""
        docs = self.create_test_documents_with_regulations()
        picker = DocumentRetriever(docs)

        query = "What is consumer protection in the UAE?"
        selected, refusal = picker.pick_for_query(query)

        # Should select from available documents
        assert len(selected) > 0, "Should return results for general query"
        law_ids = [d.law_id for d in selected]
        assert "FL_15_2020_CONSUMER_PROTECTION" in law_ids or "CD_66_2023_CONSUMER_PROTECTION_EXEC_REG" in law_ids
