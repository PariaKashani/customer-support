from datetime import date, datetime, timedelta
from typing import Optional, Union

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import tool

from .excursion_tool_handler import ExcursionToolHandler

excursion_tool_handler = ExcursionToolHandler()

class ToBookExcursion(BaseModel):
    """Transfers work to a specialized assistant to handle trip recommendation and other excursion bookings."""

    location: str = Field(
        description="The location where the user wants to book a recommended trip."
    )
    request: str = Field(
        description="Any additional information or requests from the user regarding the trip recommendation."
    )

    class Config:
        schema_extra = {
            "example": {
                "location": "Lucerne",
                "request": "The user is interested in outdoor activities and scenic views.",
            }
        }

@tool
def search_trip_recommendations(
    location: Optional[str] = None,
    name: Optional[str] = None,
    keywords: Optional[str] = None,
) -> list[dict]:
    """
    Search for trip recommendations based on location, name, and keywords. Args must be in english!
چستجو برای پیشنهادهایی برای گشت و گذار

    Args:
        location (Optional[str]): The location of the trip recommendation. Defaults to None.
        name (Optional[str]): The name of the trip recommendation. Defaults to None.
        keywords (Optional[str]): The keywords associated with the trip recommendation. Defaults to None.

    Returns:
        list[dict]: A list of trip recommendation dictionaries matching the search criteria.
    """
    return excursion_tool_handler.search_trip_recommendations(location, name, keywords)


@tool
def book_excursion(recommendation_id: int) -> str:
    """
    Book a excursion by its recommendation ID. Args must be in english!

    Args:
        recommendation_id (int): The ID of the trip recommendation to book.

    Returns:
        str: A message indicating whether the trip recommendation was successfully booked or not.
    """
    return excursion_tool_handler.book_excursion(recommendation_id)


@tool
def update_excursion(recommendation_id: int, details: str) -> str:
    """
    Update a trip recommendation's details by its ID. Args must be in english!

    Args:
        recommendation_id (int): The ID of the trip recommendation to update.
        details (str): The new details of the trip recommendation.

    Returns:
        str: A message indicating whether the trip recommendation was successfully updated or not.
    """
    return excursion_tool_handler.update_excursion(recommendation_id, details)


@tool
def cancel_excursion(recommendation_id: int) -> str:
    """
    Cancel a trip recommendation by its ID. Args must be in english!

    Args:
        recommendation_id (int): The ID of the trip recommendation to cancel.

    Returns:
        str: A message indicating whether the trip recommendation was successfully cancelled or not.
    """
    return excursion_tool_handler.cancel_excursion(recommendation_id)

def get_excursion_safe_tools():
    return [search_trip_recommendations]

def get_excursion_sensitive_tools():
    return [book_excursion, update_excursion, cancel_excursion]