from langchain_core.tools import tool
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage
from langchain_community.tools.tavily_search import TavilySearchResults

from .general_tool_handler import GeneralToolHandler
from .flight_tools import search_flights

general_tool_handler = GeneralToolHandler()

@tool
def lookup_policy(query: str) -> str:
    """Consult the company policies to check whether certain options are permitted.
    Use this before making any flight changes performing other 'write' events."""

    return general_tool_handler.lookup_policy(query)

def get_primary_assistant_tools():
    return [TavilySearchResults(max_results=1), search_flights, lookup_policy,]


def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )

