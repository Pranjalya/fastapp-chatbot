from pathlib import Path
from typing import Any, Dict, List
from pypdf import PdfReader
from app.parsers.base import BaseParser, ParsedDocument

class PDFParser(BaseParser):
    async def parse(self, file_path: Path, filename: str) -> ParsedDocument:
        reader = PdfReader(str(file_path))
        num_pages = len(reader.pages)
        pages_data: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []
        
        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            page_text = page.extract_text() or ""
            page_clean = page_text.strip()
            pages_data.append({
                "page_number": page_num,
                "text": page_clean,
                "char_count": len(page_clean)
            })
            full_text_parts.append(f"--- [Page {page_num}] ---\n{page_clean}\n")
        
        full_text = "\n".join(full_text_parts)
        token_estimate = max(1, len(full_text) // 4)
        
        # Extract outline/bookmarks if present
        outline_items: List[str] = []
        try:
            if reader.outline:
                def extract_outline(items):
                    for item in items:
                        if isinstance(item, list):
                            extract_outline(item)
                        elif hasattr(item, "title"):
                            outline_items.append(str(item.title))
                extract_outline(reader.outline)
        except Exception:
            pass
        
        toc_summary = f"PDF document with {num_pages} pages."
        if outline_items:
            toc_summary += " Table of contents: " + ", ".join(outline_items[:10])
            if len(outline_items) > 10:
                toc_summary += f" ...and {len(outline_items) - 10} more sections."
        
        return ParsedDocument(
            filename=filename,
            file_type="pdf",
            text_content=full_text,
            token_estimate=token_estimate,
            summary_or_toc=toc_summary,
            pages=pages_data,
            metadata={"num_pages": num_pages, "outline": outline_items}
        )
