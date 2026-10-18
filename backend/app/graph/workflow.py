from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from app.graph.nodes import agent_node, prepare_context_node, summarizer_node
from app.graph.state import ChatState
from app.retrieval.tools import get_document_tools

def should_summarize(state: ChatState) -> Literal["summarizer", "agent"]:
    """Decide whether to condense older messages before calling the agent."""
    messages = state.get("messages", [])
    n_turns = state.get("n_turns", 5)
    if len(messages) > n_turns * 2:
        return "summarizer"
    return "agent"

def should_continue_tools(state: ChatState) -> Literal["tools", "__end__"]:
    """Decide whether to execute tool calls or finish turn."""
    messages = state.get("messages", [])
    if not messages:
        return END
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END

def create_chat_graph():
    """Build and compile the LangGraph multi-turn conversation graph."""
    builder = StateGraph(ChatState)
    
    # Register graph nodes
    builder.add_node("prepare_context", prepare_context_node)
    builder.add_node("summarizer", summarizer_node)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(get_document_tools()))
    
    # Configure graph edges & conditional routing
    builder.add_edge(START, "prepare_context")
    builder.add_conditional_edges(
        "prepare_context",
        should_summarize,
        {"summarizer": "summarizer", "agent": "agent"}
    )
    builder.add_edge("summarizer", "agent")
    builder.add_conditional_edges(
        "agent",
        should_continue_tools,
        {"tools": "tools", END: END}
    )
    builder.add_edge("tools", "agent")
    
    # In-memory checkpointer for thread execution state
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)

# Global compiled graph instance
chat_graph = create_chat_graph()
