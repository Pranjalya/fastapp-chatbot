from typing import Annotated, Any, Dict, List, Optional
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

class ChatState(TypedDict):
    # Persistent conversational messages with LangGraph reducer
    messages: Annotated[List[AnyMessage], add_messages]
    
    # Running rolling summary for turns pruned beyond N turns
    summary: str
    
    # N-turn sliding window parameter (N conversational user-assistant turns = 2N messages)
    n_turns: int
    
    # Attached documents metadata list
    documents: List[Dict[str, Any]]
    
    # Text injected directly into prompt for small files (<= threshold)
    direct_context: str
    
    # Table of contents/manifest for large files available via tools
    large_docs_manifest: str
    
    # Thread & User identifiers
    thread_id: str
    user_id: str
    
    # Provider & model parameters (gemini, nvidia, openai, etc.)
    provider_config: Dict[str, Any]
    
    # Signal if summarization occurred during the step
    summary_updated: bool
