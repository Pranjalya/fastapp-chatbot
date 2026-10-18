from app.config import settings
from app.parsers.base import ParsedDocument

STRATEGY_DIRECT_CONTEXT = "DIRECT_CONTEXT"
STRATEGY_TOOL_RETRIEVAL = "TOOL_RETRIEVAL"

def determine_document_strategy(parsed_doc: ParsedDocument, force_tool: bool = False) -> str:
    """
    Determine whether to inject document directly into prompt context
    or index it for agentic tool reading.
    """
    if force_tool:
        return STRATEGY_TOOL_RETRIEVAL
    
    if parsed_doc.token_estimate <= settings.MAX_DIRECT_CONTEXT_TOKENS:
        return STRATEGY_DIRECT_CONTEXT
    else:
        return STRATEGY_TOOL_RETRIEVAL
