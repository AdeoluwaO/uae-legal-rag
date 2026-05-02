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
    DIFC laws use "N." at the start of a line.
    
    Returns: List of (article_number, start_position, end_position, text)
    """
    articles = []

    # For federal laws: "Article (43)", "Article (44)", etc.
    pattern = r'Article\s*\(\s*(\d+)\s*\)'

    for match in re.finditer(pattern, text):
        article_num = match.group(1)
        start = match.start()
        
        # Find where this article ends (next article or end of text)
        next_match = re.search(r'Article\s*\(\s*\d+\s*\)', text[match.end():])
        if next_match:
            end = match.end() + next_match.start()
        else:
            end = len(text)
        
        article_text = text[start:end].strip()
        articles.append((article_num, start, end, article_text))
    
    return articles

    
# Example usage:
if __name__ == "__main__":
    pdf_path = "input_corpus/data/FDL_33_2021_LABOUR.pdf"
    text = extract_text_from_pdf(pdf_path)
    print(f"Extracted {len(text)} characters from PDF")
    
    articles = find_articles(text, "FDL_33_2021_LABOUR")
    print(f"Found {len(articles)} articles")
    for article_num, _, _, article_text in articles[:3]:  # Show first 3
        print(f"\n--- Article {article_num} ---")
        print(article_text[:200])  # First 200 chars