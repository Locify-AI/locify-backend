from sqlalchemy.orm import Session
from models import Location, Narration, UserLocation
from typing import List, Optional
import math


class LocationService:
    """Service layer for location and narration operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_existing_location(self, latitude: float, longitude: float, radius_km: float = 5.0) -> Optional[UserLocation]:
        """
        Check if a location within radius_km has been discovered before.
        Uses Haversine formula for distance calculation.
        """
        # Get all user locations
        all_locations = self.db.query(UserLocation).all()
        
        for loc in all_locations:
            distance = self._haversine_distance(
                latitude, longitude,
                loc.latitude, loc.longitude
            )
            
            if distance <= radius_km:
                return loc
        
        return None
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in kilometers using Haversine formula"""
        R = 6371  # Earth's radius in kilometers
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def detect_city_name(self, latitude: float, longitude: float) -> str:
        """
        Detect city name from coordinates.
        For now, returns a simple format. In production, you'd use a geocoding service.
        """
        # TODO: Integrate with geocoding API (e.g., Nominatim, Google Geocoding)
        # For now, return a placeholder
        return f"City at ({latitude:.4f}, {longitude:.4f})"
    
    def store_locations(self, locations_data: List[dict], latitude: float, longitude: float, city_name: str) -> int:
        """
        Store discovered locations in the database.
        Returns the number of locations stored.
        """
        print(f"DEBUG: store_locations called with {len(locations_data)} locations")

        # Create or get user location entry
        user_location = UserLocation(
            latitude=latitude,
            longitude=longitude,
            city_name=city_name
        )
        self.db.add(user_location)
        self.db.flush()  # Get the ID

        stored_count = 0
        skipped_count = 0

        for i, loc_data in enumerate(locations_data):
            print(f"DEBUG: Processing location {i+1}/{len(locations_data)}: {loc_data.get('name', 'Unknown')}")
            # Extract coordinates from the received data
            coords = loc_data.get('coordinates', {})
            if isinstance(coords, dict):
                loc_lat = coords.get('latitude')
                loc_lon = coords.get('longitude')
            else:
                # Skip if coordinates are missing or invalid
                print(f"  SKIPPED: Invalid coordinates format")
                skipped_count += 1
                continue

            # Skip if no valid coordinates
            if loc_lat is None or loc_lon is None:
                print(f"  SKIPPED: Missing latitude or longitude")
                skipped_count += 1
                continue

            # Skip if name is missing
            if not loc_data.get('name'):
                print(f"  SKIPPED: Missing name")
                skipped_count += 1
                continue
            
            # Check if location already exists (by fsq_id if available, or by name+coordinates)
            existing_location = None
            if loc_data.get('fsq_id'):
                existing_location = self.db.query(Location).filter(
                    Location.fsq_id == loc_data.get('fsq_id')
                ).first()
            
            # Extract narration if present in the data
            narration_text = loc_data.get('narration', '')

            # Skip locations without narrations
            if not narration_text or narration_text.strip() == '':
                print(f"  SKIPPED: No narration available")
                skipped_count += 1
                continue

            if existing_location:
                # Update existing location with new data
                existing_location.name = loc_data.get('name', existing_location.name)
                existing_location.fsq_id = loc_data.get('fsq_id') or existing_location.fsq_id
                existing_location.category = loc_data.get('category') or existing_location.category
                existing_location.latitude = loc_lat
                existing_location.longitude = loc_lon
                existing_location.distance = str(loc_data.get('distance')) if loc_data.get('distance') else existing_location.distance
                existing_location.address = loc_data.get('address') or existing_location.address
                existing_location.rating = str(loc_data.get('rating')) if loc_data.get('rating') else existing_location.rating
                existing_location.description = loc_data.get('description') or existing_location.description
                existing_location.popularity = str(loc_data.get('popularity')) if loc_data.get('popularity') else existing_location.popularity
                existing_location.historical_significance = loc_data.get('historical_significance') or existing_location.historical_significance
                existing_location.user_location_id = user_location.id
                location_id = existing_location.id
            else:
                # Create new location - store exactly what we receive
                location = Location(
                    name=loc_data.get('name'),
                    fsq_id=loc_data.get('fsq_id'),
                    category=loc_data.get('category'),
                    latitude=loc_lat,
                    longitude=loc_lon,
                    distance=str(loc_data.get('distance')) if loc_data.get('distance') else None,
                    address=loc_data.get('address'),
                    rating=str(loc_data.get('rating')) if loc_data.get('rating') else None,
                    description=loc_data.get('description'),
                    popularity=str(loc_data.get('popularity')) if loc_data.get('popularity') else None,
                    historical_significance=loc_data.get('historical_significance'),
                    user_location_id=user_location.id
                )
                self.db.add(location)
                self.db.flush()  # Get the location ID
                location_id = location.id
                stored_count += 1
                print(f"  STORED: New location added to database")

            # Store narration if provided (after location is saved)
            if narration_text:
                existing_narration = self.db.query(Narration).filter(
                    Narration.location_id == location_id
                ).first()

                if existing_narration:
                    existing_narration.script = narration_text
                    existing_narration.word_count = len(narration_text.split())
                    print(f"  Updated narration ({len(narration_text.split())} words)")
                else:
                    narration = Narration(
                        location_id=location_id,
                        script=narration_text,
                        word_count=len(narration_text.split())
                    )
                    self.db.add(narration)
                    print(f"  Added narration ({len(narration_text.split())} words)")
            else:
                print(f"  WARNING: No narration text for this location")

        self.db.commit()
        print(f"DEBUG: Storage complete - Stored: {stored_count}, Skipped: {skipped_count} (no narration), Total: {len(locations_data)}")
        return stored_count
    
    def get_locations_by_city(self, city_name: str) -> List[Location]:
        """Get all locations for a specific city"""
        user_location = self.db.query(UserLocation).filter(
            UserLocation.city_name == city_name
        ).first()
        
        if not user_location:
            return []
        
        return self.db.query(Location).filter(
            Location.user_location_id == user_location.id
        ).all()
    
    def get_locations_near(self, latitude: float, longitude: float, radius_km: float = 10.0) -> List[Location]:
        """Get all locations within radius_km of given coordinates"""
        all_locations = self.db.query(Location).all()
        
        nearby_locations = []
        for loc in all_locations:
            distance = self._haversine_distance(
                latitude, longitude,
                loc.latitude, loc.longitude
            )
            if distance <= radius_km:
                nearby_locations.append(loc)
        
        return nearby_locations
    
    def get_all_locations(self) -> List[Location]:
        """Get all locations"""
        return self.db.query(Location).all()
    
    def get_location_by_id(self, location_id: int) -> Optional[Location]:
        """Get a location by ID"""
        return self.db.query(Location).filter(Location.id == location_id).first()
    
    def store_narration(self, location_id: int, narration_text: str) -> Narration:
        """Store narration for a location"""
        # Check if narration already exists
        existing_narration = self.db.query(Narration).filter(
            Narration.location_id == location_id
        ).first()
        
        if existing_narration:
            # Update existing narration
            existing_narration.script = narration_text
            existing_narration.word_count = len(narration_text.split())
            self.db.commit()
            return existing_narration
        
        # Create new narration
        narration = Narration(
            location_id=location_id,
            script=narration_text,
            word_count=len(narration_text.split())
        )
        self.db.add(narration)
        self.db.commit()
        self.db.refresh(narration)
        return narration
    
    def get_narration(self, location_id: int) -> Optional[Narration]:
        """Get narration for a location"""
        return self.db.query(Narration).filter(
            Narration.location_id == location_id
        ).first()

