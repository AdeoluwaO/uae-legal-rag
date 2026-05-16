from src.core.types import InstrumentType
from src.core.types import LawStatus
from src.core.types import Jurisdiction
from typing import List, Optional, Tuple
from src.core.types import Document


class DocumentRetriever:
    """
    Given a question, decide which documents apply.
    This is the "authoritative selection" logic.
    """

    # Mapping of topics to jurisdictions (federal subjects have no DIFC equivalent in corpus)
    FEDERAL_ONLY_TOPICS = {
        "aml", "anti-money laundering", "combating financing",
        "commercial companies", "companies law",
        "consumer protection", "consumer",
        "vat", "value-added tax", "taxation",
        "cybercrimes", "cybercrime", "rumours",
        "labour", "employment", "worker", "employee", "termination", "wage",
        "repealed", "old law", "1980"
    }

    # Topics exclusive to DIFC (if any in corpus)
    DIFC_ONLY_TOPICS = set()

    def __init__(self, all_documents:List[Document]):
        self.documents = {doc.law_id: doc for doc in all_documents}


    def pick_by_jurisdiction(self, query: str, candidates: List[Document]) -> List[Document]:
        """
        Determine which jurisdiction applies to the query.

        Rules in order:
        1. If query explicitly mentions DIFC → filter to DIFC documents
        2. If query explicitly mentions onshore/federal → filter to federal documents
        3. If query mentions a federal-only topic (AML, VAT, Cybercrimes, etc) → federal
        4. If query mentions a DIFC-only topic → DIFC
        5. If both jurisdiction keywords are present → ambiguous (refuse)
        6. Otherwise → no filter (both jurisdictions' documents)
        """
        query_lower = query.lower()

        keywords_onshore = ["onshore", "federal", "private sector", "mainland"]
        keywords_difc = ["difc", "free zone"]

        mentions_onshore = any(keyword in query_lower for keyword in keywords_onshore)
        mentions_difc = any(keyword in query_lower for keyword in keywords_difc)

        # Explicit jurisdiction conflict → refuse
        if mentions_onshore and mentions_difc:
            return None

        # Explicit DIFC mention
        if mentions_difc:
            return [d for d in candidates if d.jurisdiction == Jurisdiction.DIFC_FREE_ZONE]

        # Explicit onshore/federal mention
        if mentions_onshore:
            return [d for d in candidates if d.jurisdiction == Jurisdiction.FEDERAL_UAE]

        # Topic-based jurisdiction inference (no explicit keywords)
        has_federal_topic = any(topic in query_lower for topic in self.FEDERAL_ONLY_TOPICS)
        has_difc_topic = any(topic in query_lower for topic in self.DIFC_ONLY_TOPICS)

        if has_federal_topic and has_difc_topic:
            # Both federal and DIFC topics mentioned → ambiguous
            return None

        if has_federal_topic:
            return [d for d in candidates if d.jurisdiction == Jurisdiction.FEDERAL_UAE]

        if has_difc_topic:
            return [d for d in candidates if d.jurisdiction == Jurisdiction.DIFC_FREE_ZONE]

        # No jurisdiction hint found → return all candidates (let other filters decide)
        return candidates
    
    def pick_by_currency(self, query:str, candidates: List[Document]) -> List[Document]:
        """
        Filter out repealed laws UNLESS the question asks about them.
        
        If query says "used to" or "previously" allow repealed
        Otherwise only in_force laws
        """

        keywords_historical = ["used to", "previously", "1980 law", "old", "repealed"]
        query_lower = query.lower()

        wants_historical = any(kw in query_lower for kw in keywords_historical)

        if wants_historical: 
            return candidates
        else: 
            return [d for d in candidates if d.status == LawStatus.IN_FORCE]

    def pick_by_instrument_type(self, query: str, candidates: List[Document]) -> List[Document]:
        """
        If a question is about details/procedures, prefer executive
        regulation. If about general principles, prefer base law.
        
        If query mentions "regulation" or "procedure" or "detailed" prefer exec regs
        """

        keywords_detailed = ["regulation", "procedure", "detailed", "specific", "requirement"]
        query_lower = query.lower()
        
        wants_detailed = any(kw in query_lower for kw in keywords_detailed)

        if wants_detailed: 
            # Prefer cabinet_decision (executive regulations)
            executive_regulation = [d for d in candidates if d.instrument_type == InstrumentType.CABINET_DECISION]
            if executive_regulation: 
                return executive_regulation

        return candidates

    def  pick_for_query(self, query:str) -> List[Document]:
        """
        Main function: Given a question, return the right documents.
        
        Returns: (list_of_documents, refusal_reason_or_None)
        
        If you should refuse, refusal_reason will be a string.
        If you should answer, refusal_reason will be None.
        """

        candidates = list(self.documents.values())

        # Apply Rules in Order 
        candidates = self.pick_by_jurisdiction(query, candidates)
        
        if candidates is None: 
            return [], "The question could apply to either onshore UAE or DIFC free zone, which have different rules. Please specify which jurisdiction applies."
        
        candidates = self.pick_by_currency(query, candidates)

        if not candidates: 
            return [], "No applicable current laws found in the corpus."
        
        candidates = self.pick_by_instrument_type(query, candidates)

        return candidates, None 