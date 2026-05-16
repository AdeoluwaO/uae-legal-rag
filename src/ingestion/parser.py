from pypdf import PdfReader
from typing import List
import re 


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Read a PDF file and extract all text as a single string.
    
    Input: e.g input_corpus/data/FDL_33_2021_LABOUR.pdf
    Output: All text from the PDF concatenated
    """
    try: 
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""

def find_articles(text: str, law_id: str) -> List[tuple]:
    """
    Find all articles in the text.

    UAE federal laws use "Article (N)" format.
    DIFC laws use "N. DIFC" format at the start of a line.

    Returns: List of (article_number, start_position, end_position, text)
    """
    articles = []

    # Detect format by checking which pattern appears first
    federal_match = re.search(r'Article\s*\(\s*(\d+)\s*\)', text)
    difc_match = re.search(r'^\s*(\d+)\.\s+[^.\n]+$', text, re.MULTILINE)

    # Use federal format if it appears first, otherwise try DIFC format
    if federal_match and (not difc_match or federal_match.start() < difc_match.start()):
        # Federal format: "Article (43)" at the start of a line or after a newline
        pattern = r'^\s*Article\s*\(\s*(\d+)\s*\)'
        next_pattern = r'^\s*Article\s*\(\s*\d+\s*\)'
    else:
        # DIFC format: "1. Title" at line start without dots
        pattern = r'^\s*(\d+)\.\s+[^.\n]+$'
        next_pattern = r'^\s*\d+\.\s+[^.\n]+$'

    for match in re.finditer(pattern, text, re.MULTILINE):
        article_num = match.group(1)
        start = match.start()

        # Find where this article ends (next article or end of text)
        next_match = re.search(next_pattern, text[match.end():], re.MULTILINE)
        if next_match:
            end = match.end() + next_match.start()
        else:
            end = len(text)

        article_text = text[start:end].strip()
        articles.append((article_num, start, end, article_text))

    return articles