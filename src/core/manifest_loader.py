import yaml 
from typing import List 
from .types import Document, Jurisdiction, InstrumentType, LawStatus


def load_manifest(path: str) -> List[Document]:
    """
    Read baseline.yaml and turn it into Document objects.
    Input: input_corpus/baseline.yaml
    Output: List of Document objects we can use in code
    """

    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    documents = []

    for doc_dict in data['documents']:
        doc = Document(
            law_id=doc_dict['law_id'],
            filename=doc_dict['filename'],
            title=doc_dict['title'],
            jurisdiction=Jurisdiction(doc_dict['jurisdiction']),
            instrument_type=InstrumentType(doc_dict['instrument_type']),
            status=LawStatus(doc_dict['status']),
            year=doc_dict['year'],
            effective_date=doc_dict['effective_date'],
            page_count=doc_dict['page_count'],
            article_count_approx=doc_dict['article_count_approx'],
            source_note=doc_dict['source_note'],
            repealed_by=doc_dict.get('repealed_by'),
            supersedes=doc_dict.get('supersedes'),
            implements=doc_dict.get('implements'),
        )
        documents.append(doc)
    return documents
        