
import sqlite3
from datetime import date, datetime, timedelta
from typing import Optional

import pytz
from langchain_core.runnables import ensure_config
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import tool

from .flight_tool_handler import FlightToolHandler

flight_tool_handler = FlightToolHandler()

class ToFlightBookingAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle flight updates and cancellations."""

    request: str = Field(
        description="Any necessary followup questions the update flight assistant should clarify before proceeding."
    )

@tool
def fetch_user_flight_information() -> list[dict]:
    """Fetch all tickets for the user along with corresponding flight information and seat assignments.Args must be in english!

    Returns:
        A list of dictionaries where each dictionary contains the ticket details,
        associated flight details, and the seat assignments for each ticket belonging to the user.
    """
    config = ensure_config()  # Fetch from the context
    configuration = config.get("configurable", {})
    passenger_id = configuration.get("passenger_id", None)

    return flight_tool_handler.fetch_user_flight_information(passenger_id)


@tool
def search_flights(
    departure_airport: Optional[str] = None,
    arrival_airport: Optional[str] = None,
    start_time: Optional[date | datetime] = None,
    end_time: Optional[date | datetime] = None,
    limit: int = 20,
) -> list[dict]:
    """Search for flights based on departure airport, arrival airport, and departure time range. Args must be in english!"""

    return flight_tool_handler.search_flights(departure_airport,arrival_airport,start_time,end_time,limit)


@tool
def update_ticket_to_new_flight(ticket_no: str, new_flight_id: int) -> str:
    """Update the user's ticket to a new valid flight. Args must be in english!"""
    config = ensure_config()
    configuration = config.get("configurable", {})
    passenger_id = configuration.get("passenger_id", None)
    return flight_tool_handler.update_ticket_to_new_flight(ticket_no, new_flight_id, passenger_id)


@tool
def cancel_ticket(ticket_no: str) -> str:
    """Cancel the user's ticket and remove it from the database. Args must be in english!"""
    config = ensure_config()
    configuration = config.get("configurable", {})
    passenger_id = configuration.get("passenger_id", None)
    return flight_tool_handler.cancel_ticket(ticket_no, passenger_id)

def get_flight_safe_tools():
    return [search_flights]

def get_flight_sensitive_tools():
    return  [update_ticket_to_new_flight, cancel_ticket]
