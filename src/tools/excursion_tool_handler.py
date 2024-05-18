import sqlite3
from datetime import date, datetime, timedelta
from typing import Optional, Union

class ExcursionToolHandler:
    def __init__(self) -> None:
        # TODO add config here to set params
        self.db = "travel2.sqlite"

    def search_trip_recommendations(self,
        location: Optional[str] = None,
        name: Optional[str] = None,
        keywords: Optional[str] = None,
    ) -> list[dict]:
    
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()

        query = "SELECT * FROM trip_recommendations WHERE 1=1"
        params = []

        if location:
            query += " AND location LIKE ?"
            params.append(f"%{location}%")
        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
        if keywords:
            keyword_list = keywords.split(",")
            keyword_conditions = " OR ".join(["keywords LIKE ?" for _ in keyword_list])
            query += f" AND ({keyword_conditions})"
            params.extend([f"%{keyword.strip()}%" for keyword in keyword_list])

        cursor.execute(query, params)
        results = cursor.fetchall()

        conn.close()

        return [
            dict(zip([column[0] for column in cursor.description], row)) for row in results
        ]
    
    def book_excursion(self, recommendation_id: int) -> str:
   
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()

        cursor.execute(
          "UPDATE trip_recommendations SET booked = 1 WHERE id = ?", (recommendation_id,)
        )
        conn.commit()

        if cursor.rowcount > 0:
            conn.close()
            return f"Trip recommendation {recommendation_id} successfully booked."
        else:
            conn.close()
            return f"No trip recommendation found with ID {recommendation_id}."
        
    def update_excursion(self, recommendation_id: int, details: str) -> str:
    
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE trip_recommendations SET details = ? WHERE id = ?",
            (details, recommendation_id),
        )
        conn.commit()

        if cursor.rowcount > 0:
            conn.close()
            return f"Trip recommendation {recommendation_id} successfully updated."
        else:
            conn.close()
            return f"No trip recommendation found with ID {recommendation_id}."
        
    def cancel_excursion(self, recommendation_id: int) -> str:
    
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE trip_recommendations SET booked = 0 WHERE id = ?", (recommendation_id,)
        )
        conn.commit()

        if cursor.rowcount > 0:
            conn.close()
            return f"Trip recommendation {recommendation_id} successfully cancelled."
        else:
            conn.close()
            return f"No trip recommendation found with ID {recommendation_id}."
