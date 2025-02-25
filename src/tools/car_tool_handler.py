import sqlite3
from datetime import date, datetime, timedelta
from typing import Optional, Union

class CarToolHandler:
    def __init__(self) -> None:
        # TODO add config here to set params
        self.db = "travel2.sqlite"

    def search_car_rentals(self,
        location: Optional[str] = None,
        name: Optional[str] = None,
        price_tier: Optional[str] = None,
        start_date: Optional[Union[datetime, date]] = None,
        end_date: Optional[Union[datetime, date]] = None,
    ) -> list[dict]:
       
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()

        query = "SELECT * FROM car_rentals WHERE 1=1"
        params = []

        if location:
            query += " AND location LIKE ?"
            params.append(f"%{location}%")
        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
        # For our tutorial, we will let you match on any dates and price tier.
        # (since our toy dataset doesn't have much data)
        cursor.execute(query, params)
        results = cursor.fetchall()

        conn.close()

        return [
            dict(zip([column[0] for column in cursor.description], row)) for row in results
        ]
    
    def book_car_rental(self, rental_id: int) -> str:
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()

        cursor.execute("UPDATE car_rentals SET booked = 1 WHERE id = ?", (rental_id,))
        conn.commit()

        if cursor.rowcount > 0:
            conn.close()
            return f"Car rental {rental_id} successfully booked."
        else:
            conn.close()
            return f"No car rental found with ID {rental_id}."
        
    def update_car_rental(self, 
        rental_id: int,
        start_date: Optional[Union[datetime, date]] = None,
        end_date: Optional[Union[datetime, date]] = None,
    ) -> str:
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()

        if start_date:
            cursor.execute(
                "UPDATE car_rentals SET start_date = ? WHERE id = ?",
                (start_date, rental_id),
            )
        if end_date:
            cursor.execute(
                "UPDATE car_rentals SET end_date = ? WHERE id = ?", (end_date, rental_id)
            )

        conn.commit()

        if cursor.rowcount > 0:
            conn.close()
            return f"Car rental {rental_id} successfully updated."
        else:
            conn.close()
            return f"No car rental found with ID {rental_id}."
        
    def cancel_car_rental(self, rental_id: int) -> str:
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()

        cursor.execute("UPDATE car_rentals SET booked = 0 WHERE id = ?", (rental_id,))
        conn.commit()

        if cursor.rowcount > 0:
            conn.close()
            return f"Car rental {rental_id} successfully cancelled."
        else:
            conn.close()
            return f"No car rental found with ID {rental_id}."