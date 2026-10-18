from langchain_core.messages import AIMessage, HumanMessage
import pytest
from app.graph.summarizer import condense_older_turns

@pytest.mark.asyncio
async def test_summarizer_boundary_below_threshold():
    # N=2 -> threshold is 4 messages
    messages = [
        HumanMessage(content="Hello", id="1"),
        AIMessage(content="Hi there!", id="2"),
        HumanMessage(content="How are you?", id="3"),
        AIMessage(content="I am doing well.", id="4"),
    ]
    state = {
        "messages": messages,
        "n_turns": 2,
        "summary": "Existing summary",
        "provider_config": {}
    }
    summary, remove_actions = await condense_older_turns(state)
    # Since len(messages) == 4 <= 2*2, no summarization occurs
    assert summary == "Existing summary"
    assert len(remove_actions) == 0
