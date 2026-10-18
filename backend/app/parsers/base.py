from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ParsedDocument(BaseModel):
    filename: str
    file_type: str
    text_content: str
    token_estimate: int
    summary_or_toc: Optional[str] = None
    pages: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseParser(ABC):
    @abstractmethod
    async def parse(self, file_path: Path, filename: str) -> ParsedDocument:
        """Parse file content and return structured ParsedDocument."""
        pass
