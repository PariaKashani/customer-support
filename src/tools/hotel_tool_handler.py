import sqlite3
from datetime import date, datetime, timedelta
from typing import Optional, Union

class HotelToolHandler:
    def __init__(self) -> None:
        # TODO add config here to set params
        self.db = "travel2.sqlite"

    def search_hotels(self,
        location: Optional[str] = None,
        name: Optional[str] = None,
        price_tier: Optional[str] = None,
        checkin_date: Optional[Union[datetime, date]] = None,
        checkout_date: Optional[Union[datetime, date]] = None,
    ) -> list[dict]:
       
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()

        query = "SELECT * FROM hotels WHERE 1=1"
        params = []

        if location:
            query += " AND location LIKE ?"
            params.append(f"%{location}%")
        if name:    
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
            # For the sake of this tutorial, we will let you match on any dates and price tier.
        cursor.execute(query, params)
        results = cursor.fetchall()

        conn.close()

        return [
            dict(zip([column[0] for column in cursor.description], row)) for row in results
        ]
    
    def book_hotel(self, hotel_id: int) -> str:
  
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()

        cursor.execute("UPDATE hotels SET booked = 1 WHERE id = ?", (hotel_id,))
        conn.commit()

        if cursor.rowcount > 0:
            conn.close()
            return f"Hotel {hotel_id} successfully booked."
        else:
            conn.close()
            return f"No hotel found with ID {hotel_id}." 

    def update_hotel(self,
        hotel_id: int,
        checkin_date: Optional[Union[datetime, date]] = None,
        checkout_date: Optional[Union[datetime, date]] = None,
    ) -> str:

        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()

        if checkin_date:
            cursor.execute(
                "UPDATE hotels SET checkin_date = ? WHERE id = ?", (checkin_date, hotel_id)
            )   
        if checkout_date:
            cursor.execute(
                "UPDATE hotels SET checkout_date = ? WHERE id = ?",
                (checkout_date, hotel_id),
            )

        conn.commit()

        if cursor.rowcount > 0:
            conn.close()
            return f"Hotel {hotel_id} successfully updated."
        else:
            conn.close()
            return f"No hotel found with ID {hotel_id}."  

    def cancel_hotel(self, hotel_id: int) -> str:
   
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()

        cursor.execute("UPDATE hotels SET booked = 0 WHERE id = ?", (hotel_id,))
        conn.commit()

        if cursor.rowcount > 0:
            conn.close()
            return f"Hotel {hotel_id} successfully cancelled."
        else:
            conn.close()
            return f"No hotel found with ID {hotel_id}." 