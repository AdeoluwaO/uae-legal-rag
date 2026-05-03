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
    
    def __init__(self, all_documents:List[Document]):
        self.documents = {doc.law_id: doc for doc in all_documents}


    def pick_by_jurisdiction(self, query: str, candidates: List[Document]) -> List[Document]:
        """
        Does the question ask about "onshore UAE" or "DIFC free zone"?
        
        If query says "onshore" filter to federal_uae only
        If query says "DIFC" filter to difc_free_zone only
        If ambiguous and answers differ REFUSE
        """

        keywords_onshore = ["onshore", "federal", "uae", "private sector", "mainland"]
        keywords_difc = ["difc", "free zone"]

        query_lower = query.lower()


        mentions_onshore = any(keyword in query_lower for keyword in keywords_onshore)
        mentions_difc = any(keyword in query_lower for keyword in keywords_difc)

        if mentions_onshore and mentions_difc: 
            return None # Ambiguous - REFUSE

        if mentions_difc:
            return [d for d in candidates if d.jurisdiction == Jurisdiction.DIFC_FREE_ZONE]
        
        if mentions_onshore: 
            return [d for d in candidates if d.jurisdiction == Jurisdiction.FEDERAL_UAE]
    
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