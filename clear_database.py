#!/usr/bin/env python3
"""
Script to clear all data from the database.
This will delete all records from all tables but keep the table structure.
"""

from database import SessionLocal, engine
from models import UserLocation, Location, Narration
from sqlalchemy import text

def clear_database():
    """Clear all data from all tables"""
    db = SessionLocal()
    try:
        # Delete in reverse order of foreign key dependencies
        # 1. Delete narrations (has foreign key to locations)
        narration_count = db.query(Narration).count()
        db.query(Narration).delete()
        print(f"Deleted {narration_count} narration(s)")
        
        # 2. Delete locations (has foreign key to user_locations)
        location_count = db.query(Location).count()
        db.query(Location).delete()
        print(f"Deleted {location_count} location(s)")
        
        # 3. Delete user_locations
        user_location_count = db.query(UserLocation).count()
        db.query(UserLocation).delete()
        print(f"Deleted {user_location_count} user location(s)")
        
        # Commit the changes
        db.commit()
        print("\n✅ Database cleared successfully!")
        print(f"Total records deleted: {narration_count + location_count + user_location_count}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error clearing database: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Clearing database...")
    clear_database()

