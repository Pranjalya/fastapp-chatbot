from app.parsers.base import ParsedDocument
from app.retrieval.router import STRATEGY_DIRECT_CONTEXT, STRATEGY_TOOL_RETRIEVAL, determine_document_strategy

def test_determine_document_strategy():
    # Small file: <= 2500 tokens -> DIRECT_CONTEXT
    small_doc = ParsedDocument(
        filename="notes.txt",
        file_type="txt",
        text_content="Short note",
        token_estimate=500
    )
    assert determine_document_strategy(small_doc) == STRATEGY_DIRECT_CONTEXT

    # Large file: > 2500 tokens -> TOOL_RETRIEVAL
    large_doc = ParsedDocument(
        filename="big_manual.pdf",
        file_type="pdf",
        text_content="Large content" * 1000,
        token_estimate=4000
    )
    assert determine_document_strategy(large_doc) == STRATEGY_TOOL_RETRIEVAL

    # Force tool override
    assert determine_document_strategy(small_doc, force_tool=True) == STRATEGY_TOOL_RETRIEVAL
