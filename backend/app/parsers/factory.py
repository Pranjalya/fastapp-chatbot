from pathlib import Path
from app.parsers.base import BaseParser
from app.parsers.docx_parser import DocxParser
from app.parsers.pdf_parser import PDFParser
from app.parsers.tabular_parser import TabularParser
from app.parsers.text_parser import TextParser

def get_parser_for_file(filepath_or_ext: str) -> BaseParser:
    """Return the suitable parser instance based on file extension."""
    ext = Path(filepath_or_ext).suffix.lower()
    
    if ext == ".pdf":
        return PDFParser()
    elif ext in [".docx", ".doc"]:
        return DocxParser()
    elif ext in [".csv", ".tsv", ".xlsx", ".xls"]:
        return TabularParser()
    else:
        # Defaults to TextParser for .txt, .md, .json, .py, .js, .html, .css, etc.
        return TextParser()
