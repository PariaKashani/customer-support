from typing import Callable, Annotated, Literal, Optional, List

from langchain_core.pydantic_v1 import BaseModel
from langchain_core.messages import ToolMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import tools_condition

from .models.state import State
from .tools.flight_tools import fetch_user_flight_information
from .tools.flight_tools import ToFlightBookingAssistant
from .tools.car_rental_tools import ToBookCarRental
from .tools.hotel_booking_tools import ToHotelBookingAssistant
from .tools.excursion_booking_tools import ToBookExcursion

class CompleteOrEscalate(BaseModel):
    """A tool to mark the current task as completed and/or to escalate control of the dialog to the main assistant,
    who can re-route the dialog based on the user's needs."""

    cancel: bool = True
    reason: str

    class Config:
        schema_extra = {
            "example": {
                "cancel": True,
                "reason": "User changed their mind about the current task.",
            },
            "example 2": {
                "cancel": True,
                "reason": "I have fully completed the task.",
            },
            "example 3": {
                "cancel": False,
                "reason": "I need to search the user's emails or calendar for more information.",
            },
        }

def create_entry_node(assistant_name: str, new_dialog_state: str) -> Callable:
    def entry_node(state: State) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "messages": [
                ToolMessage(
                    content=f"The assistant is now the {assistant_name}. Reflect on the above conversation between the host assistant and the user."
                    f" The user's intent is unsatisfied. Use the provided tools to assist the user. Remember, you are {assistant_name},"
                    " and the booking, update, other other action is not complete until after you have successfully invoked the appropriate tool."
                    " If the user changes their mind or needs help for other tasks, call the CompleteOrEscalate function to let the primary host assistant take control."
                    " Do not mention who you are - just act as the proxy for the assistant.",
                    tool_call_id=tool_call_id,
                )
            ],
            "dialog_state": new_dialog_state,
        }

    return entry_node

def user_info(state: State):
    return {"user_info": fetch_user_flight_information.invoke({})}

def create_route(safe_tools: List, route_name: str, type_hint) -> Callable:
    def route_skill(
        state: State,
    ) -> type_hint:
        route = tools_condition(state)
        if route == END:
            return END
        tool_calls = state["messages"][-1].tool_calls
        did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
        if did_cancel:
            return "leave_skill"
        safe_toolnames = [t.name for t in safe_tools]
        if all(tc["name"] in safe_toolnames for tc in tool_calls):
            return route_name + "_safe_tools"
        return route_name + "_sensitive_tools"
    
    return route_skill

# This node will be shared for exiting all specialized assistants
def pop_dialog_state(state: State) -> dict:
    """Pop the dialog stack and return to the main assistant.

    This lets the full graph explicitly track the dialog flow and delegate control
    to specific sub-graphs.
    """
    messages = []
    if state["messages"][-1].tool_calls:
        # Note: Doesn't currently handle the edge case where the llm performs parallel tool calls
        messages.append(
            ToolMessage(
                content="Resuming dialog with the host assistant. Please reflect on the past conversation and assist the user as needed.",
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
            )
        )
    return {
        "dialog_state": "pop",
        "messages": messages,
    }

def route_primary_assistant(
    state: State,
) -> Literal[
    "primary_assistant_tools",
    "enter_update_flight",
    "enter_book_hotel",
    "enter_book_excursion",
    "enter_book_car_rental"
    "__end__",
]:
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    
    if tool_calls:
        if len(tool_calls)>0:
            tool_calls = [tool_calls[0]]
        if tool_calls[0]["name"] == "multi_tool_use.parallel":
            # a multi tool use has happened and we should decide what we're gonna do as next step
            # at this step I just select one of the tool calls and ignore the other one
            # TODO manage this situation better
            tool_calls[0]["name"] = tool_calls[0]["args"]["tool_uses"][0]["recipient_name"]
            tool_calls[0]["args"] = tool_calls[0]["args"]["tool_uses"][0]["parameters"]

        state["messages"][-1].tool_calls = tool_calls
        
        if tool_calls[0]["name"] == ToFlightBookingAssistant.__name__:
            return "enter_update_flight"
        elif tool_calls[0]["name"] == ToBookCarRental.__name__:
            return "enter_book_car_rental"
        elif tool_calls[0]["name"] == ToHotelBookingAssistant.__name__:
            return "enter_book_hotel"
        elif tool_calls[0]["name"] == ToBookExcursion.__name__:
            return "enter_book_excursion"
        
        return "primary_assistant_tools"
    raise ValueError("Invalid route")

# Each delegated workflow can directly respond to the user
# When the user responds, we want to return to the currently active workflow
def route_to_workflow(
    state: State,
    ) -> Literal[
    "primary_assistant",
    "update_flight",
    "book_car_rental",
    "book_hotel",
    "book_excursion",
    ]:
    """If we are in a delegated state, route directly to the appropriate assistant."""
    dialog_state = state.get("dialog_state")
    if not dialog_state:
        return "primary_assistant"
    return dialog_state[-1]