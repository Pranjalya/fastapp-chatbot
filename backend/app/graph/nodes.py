import logging
from typing import Any, Dict
from langchain_core.messages import SystemMessage
from app.core.llm_factory import get_chat_model
from app.graph.state import ChatState
from app.graph.summarizer import condense_older_turns
from app.retrieval.tools import get_document_tools

logger = logging.getLogger(__name__)

async def prepare_context_node(state: ChatState) -> Dict[str, Any]:
    """Prepares direct context text and large document manifests for the prompt."""
    documents = state.get("documents", [])
    direct_parts = []
    manifest_parts = []
    
    for doc in documents:
        strategy = doc.get("strategy")
        filename = doc.get("filename", "unknown")
        doc_id = doc.get("doc_id", "")
        
        if strategy == "DIRECT_CONTEXT":
            text_content = doc.get("text_content", "")
            direct_parts.append(f"<document id='{doc_id}' filename='{filename}'>\n{text_content}\n</document>")
        elif strategy == "TOOL_RETRIEVAL":
            summary = doc.get("summary_or_toc", "Large document")
            tokens = doc.get("token_count_estimate", 0)
            manifest_parts.append(
                f"- Document ID: '{doc_id}' | File: '{filename}' | Tokens: ~{tokens} | Summary/TOC: {summary}"
            )
            
    direct_context = "\n\n".join(direct_parts)
    large_docs_manifest = "\n".join(manifest_parts)
    
    return {
        "direct_context": direct_context,
        "large_docs_manifest": large_docs_manifest,
        "summary_updated": False,
    }

async def summarizer_node(state: ChatState) -> Dict[str, Any]:
    """Condenses turns older than 2*N into a persistent rolling summary."""
    new_summary, remove_actions = await condense_older_turns(state)
    return {
        "summary": new_summary,
        "messages": remove_actions,
        "summary_updated": bool(remove_actions),
    }

async def agent_node(state: ChatState) -> Dict[str, Any]:
    """Invokes LLM with bound document tools and structured context prompt."""
    provider_cfg = state.get("provider_config", {})
    llm = get_chat_model(
        provider=provider_cfg.get("provider"),
        model_name=provider_cfg.get("model_name"),
        api_key=provider_cfg.get("api_key"),
        base_url=provider_cfg.get("base_url"),
        temperature=provider_cfg.get("temperature", 0.3),
        streaming=True
    )
    
    # Bind document inspection tools
    tools = get_document_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    # Assemble comprehensive system prompt
    system_sections = [
        "You are an advanced, intelligent AI Assistant with document analysis and multi-turn conversational capabilities."
    ]
    
    summary = state.get("summary", "").strip()
    if summary:
        system_sections.append(
            f"### CONVERSATION SUMMARY OF OLDER TURNS:\n{summary}\n"
            "(Use this summary for past context and background facts without needing to re-ask the user.)"
        )
        
    direct_context = state.get("direct_context", "").strip()
    if direct_context:
        system_sections.append(
            f"### DIRECTLY ATTACHED DOCUMENTS (Small Files):\n{direct_context}\n"
            "(These documents are small and provided in full. Reference them directly in your answers.)"
        )
        
    manifest = state.get("large_docs_manifest", "").strip()
    if manifest:
        system_sections.append(
            f"### LARGE DOCUMENTS AVAILABLE VIA TOOLS:\n{manifest}\n"
            "INSTRUCTIONS FOR LARGE DOCUMENTS:\n"
            "- The files above are large and indexed for on-demand inspection.\n"
            "- When the user asks questions concerning these documents, call your tools:\n"
            "  * `search_document(doc_id, query)` to find relevant excerpts,\n"
            "  * `read_document_page(doc_id, page_number)` to read specific pages/sections in full,\n"
            "  * `inspect_document_outline(doc_id)` to review the table of contents.\n"
            "- Always cite the document name and page/section number when referencing findings."
        )
        
    system_prompt = "\n\n".join(system_sections)
    
    # Prepend SystemMessage to messages for execution
    active_messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
    
    response = await llm_with_tools.ainvoke(active_messages)
    return {"messages": [response]}
