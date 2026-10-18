from typing import List
from langchain_core.tools import tool
from app.retrieval.hybrid_store import document_registry

@tool
def search_document(doc_id: str, query: str) -> str:
    """
    Search inside a large attached document using keyword/semantic retrieval.
    Args:
        doc_id: The unique ID of the document to search.
        query: Specific terms or question to search for in the document.
    Returns:
        The most relevant passages from the document with page/section numbers.
    """
    index = document_registry.get(doc_id)
    if not index:
        return f"Error: Document with ID '{doc_id}' is not indexed or found."
    
    results = index.search(query, top_k=4)
    if not results:
        return f"No relevant content found for query '{query}' in document {doc_id}."
    
    formatted = [f"Found {len(results)} relevant sections in document '{index.parsed_doc.filename}':\n"]
    for idx, r in enumerate(results, 1):
        page_info = f"Page {r['page']}" if r.get("page") else f"Section {r['chunk_id'] + 1}"
        formatted.append(f"[{idx}] ({page_info}):\n{r['text']}\n")
    
    return "\n".join(formatted)

@tool
def read_document_page(doc_id: str, page_number: int) -> str:
    """
    Read the complete content of a specific page or section in an attached document.
    Args:
        doc_id: The unique ID of the document.
        page_number: The 1-based page or section number to read.
    """
    index = document_registry.get(doc_id)
    if not index:
        return f"Error: Document with ID '{doc_id}' is not found."
    
    return index.read_page(page_number)

@tool
def inspect_document_outline(doc_id: str) -> str:
    """
    Inspect the high-level outline, table of contents, or structural summary of an attached document.
    Args:
        doc_id: The unique ID of the document.
    """
    index = document_registry.get(doc_id)
    if not index:
        return f"Error: Document with ID '{doc_id}' is not found."
    
    return index.get_outline()

def get_document_tools() -> List:
    """Return all document query tools."""
    return [search_document, read_document_page, inspect_document_outline]
