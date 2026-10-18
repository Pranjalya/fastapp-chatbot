from pathlib import Path
from charset_normalizer import from_bytes
from app.parsers.base import BaseParser, ParsedDocument

class TextParser(BaseParser):
    async def parse(self, file_path: Path, filename: str) -> ParsedDocument:
        with open(file_path, "rb") as f:
            raw_data = f.read()
        
        # Try UTF-8 first, fallback to charset detection
        try:
            content = raw_data.decode("utf-8")
        except UnicodeDecodeError:
            detection = from_bytes(raw_data).best()
            content = str(detection) if detection else raw_data.decode("latin1", errors="replace")
        
        lines = content.splitlines()
        line_count = len(lines)
        token_estimate = max(1, len(content) // 4)
        
        summary = f"Text document with {line_count} lines, approximately {token_estimate} tokens."
        
        return ParsedDocument(
            filename=filename,
            file_type=file_path.suffix.lstrip(".").lower() or "txt",
            text_content=content,
            token_estimate=token_estimate,
            summary_or_toc=summary,
            metadata={"line_count": line_count, "char_count": len(content)}
        )
