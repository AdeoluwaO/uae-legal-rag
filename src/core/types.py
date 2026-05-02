from enum import Enum
from dataclasses import dataclass
from typing import Optional


class Jurisdiction(Enum):
    FEDERAL_UAE = "federal_uae"
    DIFC_FREE_ZONE = "difc_free_zone"


class InstrumentType(Enum):
    FEDERAL_LAW = "federal_law"
    FEDERAL_DECREE_LAW = "federal_decree_law"
    CABINET_DECISION = "cabinet_decision"
    DIFC_LAW = "difc_law"


class LawStatus(Enum):
    IN_FORCE = "in_force"
    REPEALED = "repealed"


@dataclass
class Document:
    """Represents one law from the manifest"""
    law_id: str 
    filename: str
    title: str
    jurisdiction: Jurisdiction  
    instrument_type: InstrumentType  
    status: LawStatus
    year: int
    effective_date: str
    page_count: int
    article_count_approx: int
    source_note: str
    
    repealed_by: Optional[str] = None  
    supersedes: Optional[str] = None  
    implements: Optional[str] = None  


@dataclass
class Article:
    """One article extracted from a PDF"""
    law_id: str
    article_number: str 
    text: str
    page_number: int
    paragraph_number: Optional[str] = None


@dataclass
class Citation:
    """A reference to an article in an answer"""
    law_id: str
    article: str
    page: int
    quote: str 
    is_verbatim: bool 
    paragraph: Optional[str] = None
