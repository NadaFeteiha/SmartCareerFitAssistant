import pdfplumber
from io import BytesIO

def extract_text_from_pdf(file) -> str:
    """
    Extract plain text from a PDF.
    Accepts either a file path (str) or a file-like object (BytesIO / Streamlit UploadedFile).
    """
    text_parts = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)
