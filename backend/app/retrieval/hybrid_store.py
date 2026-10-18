import re
from typing import Any, Dict, List, Optional
from rank_bm25 import BM25Okapi
from app.parsers.base import ParsedDocument

class DocumentIndex:
    def __init__(self, doc_id: str, parsed_doc: ParsedDocument):
        self.doc_id = doc_id
        self.parsed_doc = parsed_doc
        self.chunks: List[Dict[str, Any]] = []
        self.tokenized_corpus: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"\w+", text)]

    def _build_index(self):
        # If document already has pages (e.g. PDF), use pages as chunks
        if self.parsed_doc.pages:
            for p in self.parsed_doc.pages:
                text = p.get("text", "")
                if text.strip():
                    self.chunks.append({
                        "chunk_id": len(self.chunks),
                        "page": p.get("page_number", 1),
                        "text": text,
                        "token_count": max(1, len(text) // 4)
                    })
        else:
            # Chunk by paragraphs or windows of ~500 tokens
            raw_paragraphs = [p.strip() for p in self.parsed_doc.text_content.split("\n\n") if p.strip()]
            current_chunk = []
            current_len = 0
            
            for p in raw_paragraphs:
                p_len = len(p)
                if current_len + p_len > 2000 and current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    self.chunks.append({
                        "chunk_id": len(self.chunks),
                        "page": None,
                        "text": chunk_text,
                        "token_count": max(1, len(chunk_text) // 4)
                    })
                    current_chunk = [p]
                    current_len = p_len
                else:
                    current_chunk.append(p)
                    current_len += p_len
            
            if current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                self.chunks.append({
                    "chunk_id": len(self.chunks),
                    "page": None,
                    "text": chunk_text,
                    "token_count": max(1, len(chunk_text) // 4)
                })

        # Build BM25 index
        if self.chunks:
            self.tokenized_corpus = [self._tokenize(c["text"]) for c in self.chunks]
            self.bm25 = BM25Okapi(self.tokenized_corpus)

    def search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        if not self.bm25 or not self.chunks:
            return []
        tokens = self._tokenize(query)
        if not tokens:
            return self.chunks[:top_k]
        
        scores = self.bm25.get_scores(tokens)
        scored_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results = []
        for idx in scored_indices[:top_k]:
            if scores[idx] > 0.05 or len(results) == 0:
                item = dict(self.chunks[idx])
                item["score"] = float(scores[idx])
                results.append(item)
        return results

    def read_page(self, page_number: int) -> str:
        if self.parsed_doc.pages:
            for p in self.parsed_doc.pages:
                if p.get("page_number") == page_number:
                    return f"--- Content of Page {page_number} ---\n{p.get('text', '')}"
            return f"Page {page_number} not found. Document has {len(self.parsed_doc.pages)} pages."
        else:
            # Fallback to chunk index if pages don't exist
            if 1 <= page_number <= len(self.chunks):
                return f"--- Section {page_number} of {len(self.chunks)} ---\n{self.chunks[page_number - 1]['text']}"
            return f"Section {page_number} not found. Total sections: {len(self.chunks)}."

    def get_outline(self) -> str:
        return self.parsed_doc.summary_or_toc or f"Document {self.parsed_doc.filename} with {len(self.chunks)} sections."

class HybridStoreRegistry:
    """In-memory store of indexed documents across active sessions."""
    def __init__(self):
        self._stores: Dict[str, DocumentIndex] = {}

    def register(self, doc_id: str, parsed_doc: ParsedDocument) -> DocumentIndex:
        index = DocumentIndex(doc_id, parsed_doc)
        self._stores[doc_id] = index
        return index

    def get(self, doc_id: str) -> Optional[DocumentIndex]:
        return self._stores.get(doc_id)

    def remove(self, doc_id: str):
        self._stores.pop(doc_id, None)

# Singleton global registry
document_registry = HybridStoreRegistry()
