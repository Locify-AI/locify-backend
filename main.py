from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from contextlib import asynccontextmanager
import uvicorn
from sqlalchemy.orm import Session

from database import SessionLocal, engine, init_db
from models import Base, Location, Narration, UserLocation
from agents import discover_locations_with_narrations as agent_discover_locations
from services import LocationService
import json
import re

import random
import base64
import os
import requests
import time
from dotenv import load_dotenv

import boto3
from botocore.exceptions import NoCredentialsError

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

def upload_video_to_s3(video_bytes: bytes, filename: str) -> str:
    """
    Uploads video bytes to S3 and returns a temporary signed URL (valid 24 hours).
    Keeps bucket private.
    """
    bucket = os.getenv("S3_BUCKET_NAME")
    try:
        # Upload video to S3 (private)
        s3.put_object(
            Bucket=bucket,
            Key=filename,
            Body=video_bytes,
            ContentType="video/mp4"
        )

        # Generate presigned URL valid for 24 hours
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": filename},
            ExpiresIn=86400  # 24 hours
        )
        return url
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not configured correctly")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    init_db()
    yield
    # Shutdown (if needed)


app = FastAPI(
    title="Locify Backend API",
    description="Tour guide app backend with MCP agent integration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Request/Response Models
class LocationRequest(BaseModel):
    latitude: float
    longitude: float
    radius: int = 1000
    user_id: Optional[str] = None


class LocationWithNarration(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    category: Optional[str] = None
    narration: str
    fsq_id: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None


class LocationResponse(BaseModel):
    message: str
    locations: List[LocationWithNarration] = []


@app.get("/")
async def root():
    return {"message": "Locify Backend API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


# ============================================================================
# CRUD ENDPOINTS FOR LOCATIONS AND NARRATIONS
# ============================================================================

@app.get("/api/cities")
async def get_all_cities(db: Session = Depends(get_db)):
    """
    Get all discovered cities/towns with their discovery info.
    Locations are grouped by city_name (within 5km radius).
    """
    location_service = LocationService(db)
    user_locations = db.query(UserLocation).all()

    cities = []
    for user_loc in user_locations:
        location_count = db.query(Location).filter(
            Location.user_location_id == user_loc.id
        ).count()

        cities.append({
            "id": user_loc.id,
            "city_name": user_loc.city_name,
            "latitude": user_loc.latitude,
            "longitude": user_loc.longitude,
            "discovered_at": user_loc.discovered_at.isoformat() if user_loc.discovered_at else None,
            "location_count": location_count
        })

    return {"cities": cities, "total": len(cities)}


@app.get("/api/cities/{city_name}/locations")
async def get_locations_by_city(city_name: str, db: Session = Depends(get_db)):
    """
    Get all locations for a specific city.
    Returns locations with their narrations.
    """
    location_service = LocationService(db)
    locations = location_service.get_locations_by_city(city_name)

    result_locations = []
    for loc in locations:
        narration = location_service.get_narration(loc.id)
        result_locations.append({
            "id": loc.id,
            "name": loc.name,
            "fsq_id": loc.fsq_id,
            "category": loc.category,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "address": loc.address,
            "description": loc.description,
            "rating": loc.rating,
            "distance": loc.distance,
            "popularity": loc.popularity,
            "historical_significance": loc.historical_significance,
            "narration": narration.script if narration else None,
            "narration_word_count": narration.word_count if narration else None,
            "created_at": loc.created_at.isoformat() if loc.created_at else None
        })

    return {
        "city_name": city_name,
        "locations": result_locations,
        "total": len(result_locations)
    }


@app.get("/api/locations/{location_id}")
async def get_location_by_id(location_id: int, db: Session = Depends(get_db)):
    """
    Get a specific location by ID with its narration.
    """
    location_service = LocationService(db)
    location = location_service.get_location_by_id(location_id)

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    narration = location_service.get_narration(location.id)

    return {
        "id": location.id,
        "name": location.name,
        "fsq_id": location.fsq_id,
        "category": location.category,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "address": location.address,
        "description": location.description,
        "rating": location.rating,
        "distance": location.distance,
        "popularity": location.popularity,
        "historical_significance": location.historical_significance,
        "narration": narration.script if narration else None,
        "narration_word_count": narration.word_count if narration else None,
        "created_at": location.created_at.isoformat() if location.created_at else None,
        "updated_at": location.updated_at.isoformat() if location.updated_at else None
    }


@app.get("/api/locations")
async def get_all_locations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all locations with pagination.
    """
    location_service = LocationService(db)
    all_locations = location_service.get_all_locations()

    # Apply pagination
    paginated_locations = all_locations[skip:skip + limit]

    result_locations = []
    for loc in paginated_locations:
        narration = location_service.get_narration(loc.id)
        result_locations.append({
            "id": loc.id,
            "name": loc.name,
            "category": loc.category,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "has_narration": narration is not None,
            "created_at": loc.created_at.isoformat() if loc.created_at else None
        })

    return {
        "locations": result_locations,
        "total": len(all_locations),
        "skip": skip,
        "limit": limit
    }


@app.delete("/api/locations/{location_id}")
async def delete_location(location_id: int, db: Session = Depends(get_db)):
    """
    Delete a specific location and its narration.
    """
    location_service = LocationService(db)
    location = location_service.get_location_by_id(location_id)

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    # Delete narration first (due to foreign key)
    narration = location_service.get_narration(location_id)
    if narration:
        db.delete(narration)

    # Delete location
    db.delete(location)
    db.commit()

    return {"message": f"Location '{location.name}' deleted successfully"}


@app.delete("/api/cities/{city_name}")
async def delete_city(city_name: str, db: Session = Depends(get_db)):
    """
    Delete a city and all its locations/narrations.
    """
    # Find the user_location
    user_location = db.query(UserLocation).filter(
        UserLocation.city_name == city_name
    ).first()

    if not user_location:
        raise HTTPException(status_code=404, detail="City not found")

    # Get all locations for this city
    locations = db.query(Location).filter(
        Location.user_location_id == user_location.id
    ).all()

    # Delete narrations and locations
    for loc in locations:
        narration = db.query(Narration).filter(
            Narration.location_id == loc.id
        ).first()
        if narration:
            db.delete(narration)
        db.delete(loc)

    # Delete user_location
    db.delete(user_location)
    db.commit()

    return {
        "message": f"City '{city_name}' and {len(locations)} locations deleted successfully"
    }


@app.post("/api/discover-locations", response_model=LocationResponse)
async def discover_locations_with_narrations(
    request: LocationRequest,
    db: Session = Depends(get_db)
):
    """
    Single endpoint that discovers historical locations (up to 20) and generates 
    narrations for each. Returns name, coordinates, category, and narration.
    """
    try:
        location_service = LocationService(db)
        
        # Check if this location (city/town) has been discovered before
        existing_location = location_service.check_existing_location(
            request.latitude,
            request.longitude,
            radius_km=5.0
        )
        
        if existing_location:
            # City already discovered, get existing locations with narrations
            locations = location_service.get_locations_by_city(existing_location.city_name)
            result_locations = []

            for loc in locations:
                # Get narration
                narration = location_service.get_narration(loc.id)
                if narration:
                    result_locations.append(LocationWithNarration(
                        id=loc.id,
                        name=loc.name,
                        latitude=loc.latitude,
                        longitude=loc.longitude,
                        category=loc.category,
                        narration=narration.script,
                        fsq_id=loc.fsq_id,
                        address=loc.address,
                        description=loc.description
                    ))

            return LocationResponse(
                message="Returning existing locations with narrations",
                locations=result_locations
            )
        
        # New city/town detected - discover locations and generate narrations in one call
        print(f"Discovering locations with narrations for new city at ({request.latitude}, {request.longitude})")
        
        # Call the combined MCP agent to discover locations and generate narrations
        result = await agent_discover_locations(
            latitude=request.latitude,
            longitude=request.longitude,
            radius=request.radius
        )
        
        # Parse JSON from the response
        locations_data = parse_json_from_response(result)

        if not locations_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to parse locations from MCP agent response"
            )

        print(f"INFO: Parsed {len(locations_data)} locations from agent response")

        # Warn if we got very few locations
        if len(locations_data) < 5:
            print(f"WARNING: Only {len(locations_data)} locations returned. Expected at least 10.")
            print(f"WARNING: This may indicate an issue with the agent or Foursquare API.")
            print(f"WARNING: Possible causes:")
            print(f"  - Limited historical sites in the area")
            print(f"  - Agent not executing all search queries")
            print(f"  - Foursquare API rate limits or availability issues")
            print(f"  - Agent filtering too aggressively")

        # If we have NO locations, raise an error
        if len(locations_data) == 0:
            raise HTTPException(
                status_code=404,
                detail="No historical locations found in this area. Try a different location or increase the search radius."
            )

        # If we have very few locations (1-3), try with increased radius
        if len(locations_data) < 4:
            print(f"INFO: Attempting fallback with increased radius (3km instead of {request.radius}m)")
            try:
                fallback_result = await agent_discover_locations(
                    latitude=request.latitude,
                    longitude=request.longitude,
                    radius=3000  # 3km fallback
                )
                fallback_locations = parse_json_from_response(fallback_result)
                if len(fallback_locations) > len(locations_data):
                    print(f"INFO: Fallback successful - got {len(fallback_locations)} locations")
                    locations_data = fallback_locations
                else:
                    print(f"INFO: Fallback didn't improve results, using original {len(locations_data)} locations")
            except Exception as e:
                print(f"WARNING: Fallback attempt failed: {str(e)}, using original {len(locations_data)} locations")

        # Limit to 20 locations
        locations_data = locations_data[:20]
        print(f"INFO: Using {len(locations_data)} locations (after limit of 20)")
        
        # Store locations and narrations in database
        city_name = location_service.detect_city_name(request.latitude, request.longitude)
        stored_count = location_service.store_locations(
            locations_data,
            request.latitude,
            request.longitude,
            city_name
        )
        
        # Fetch the stored locations (narrations are already stored by store_locations)
        print(f"INFO: Fetching stored locations for city: {city_name}")
        stored_locations = location_service.get_locations_by_city(city_name)
        print(f"INFO: Found {len(stored_locations)} stored locations")

        # Build response with locations and their narrations
        result_locations = []
        for loc in stored_locations:
            # Get narration from database (already stored by store_locations)
            narration = location_service.get_narration(loc.id)

            if narration:
                result_locations.append(LocationWithNarration(
                    id=loc.id,
                    name=loc.name,
                    latitude=loc.latitude,
                    longitude=loc.longitude,
                    category=loc.category,
                    narration=narration.script,
                    fsq_id=loc.fsq_id,
                    address=loc.address,
                    description=loc.description
                ))

        print(f"INFO: Built response with {len(result_locations)} locations")
        print(f"INFO: Returning response to client...")

        response = LocationResponse(
            message=f"Discovered {len(result_locations)} locations with narrations",
            locations=result_locations
        )

        print(f"INFO: Response created successfully")
        return response
        
    except Exception as e:
        print(f"Error in discover_locations_with_narrations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")




def parse_json_from_response(response_text: str) -> List[dict]:
    """
    Parse JSON array from the MCP agent response.
    Handles cases where the response may contain markdown code blocks or extra text.
    """
    if not response_text:
        return []
    
    # Clean up the response text
    response_text = response_text.strip()
    
    # Strategy 1: Try to extract JSON from markdown code blocks first
    code_block_patterns = [
        r'```(?:json)?\s*(\[[\s\S]*?\])\s*```',  # Standard markdown code block
        r'```\s*(\[[\s\S]*?\])\s*```',  # Code block without json tag
        r'`(\[[\s\S]*?\])`',  # Inline code
    ]
    
    for pattern in code_block_patterns:
        match = re.search(pattern, response_text, re.DOTALL)
        if match:
            try:
                json_str = match.group(1).strip()
                data = json.loads(json_str)
                if isinstance(data, list) and len(data) > 0:
                    return data
            except (json.JSONDecodeError, IndexError):
                continue
    
    # Strategy 2: Try to find JSON array pattern in the text
    json_array_pattern = r'\[[\s\S]*?\]'
    matches = list(re.finditer(json_array_pattern, response_text, re.DOTALL))
    
    # Try the largest match first (most likely to be complete)
    if matches:
        for match in sorted(matches, key=lambda m: len(m.group(0)), reverse=True):
            try:
                json_str = match.group(0).strip()
                data = json.loads(json_str)
                if isinstance(data, list) and len(data) > 0:
                    return data
            except json.JSONDecodeError:
                continue
    
    # Strategy 3: Try parsing the entire response as JSON
    try:
        data = json.loads(response_text)
        if isinstance(data, list) and len(data) > 0:
            return data
        elif isinstance(data, dict) and 'locations' in data:
            # Handle case where JSON is wrapped in an object
            if isinstance(data['locations'], list):
                return data['locations']
    except json.JSONDecodeError:
        pass
    
    # Strategy 4: Try to find and extract multiple JSON objects/arrays
    # Look for content between square brackets that might be JSON
    bracket_content = re.findall(r'\{[^{}]*"name"[^{}]*\}', response_text)
    if bracket_content:
        try:
            # Try to reconstruct a JSON array from individual objects
            objects = []
            for content in bracket_content:
                try:
                    obj = json.loads(content)
                    if isinstance(obj, dict) and 'name' in obj:
                        objects.append(obj)
                except json.JSONDecodeError:
                    continue
            if objects:
                return objects
        except Exception:
            pass
    
    print(f"Warning: Could not parse JSON from response. First 500 chars: {response_text[:500]}")
    return []

DID_API_KEY = os.getenv("DID_API_KEY")

guides = [
    "JBFqnCBsd6RMkjVDRZzb",  # george british
    "IKne3meq5aSn9XLyUdCD",  # charlie australian
    "cgSgspJ2msm6clMCkdW9",  # jessica american
    "pFZP5JQG7iQjIQuC4Bku",  # lily british
    "nPczCjzI2devNBz1zQrb",  # brian american
]

images = [
    "blackguy.jpeg",
    "brownguy.jpg",
    "asiangirl.jpg",
    "whitegirl.jpg",
    "whiteguy.jpeg",
]


class AvatarRequest(BaseModel):
    text: str = "Hi, and welcome to your new favorite city!"


@app.post("/api/generate-talking-avatar")
async def generate_talking_avatar(request: AvatarRequest):
    """
    Create a talking avatar video using D-ID with a random voice and avatar.
    """
    try:
        headers = {
            "Authorization": f"Basic {base64.b64encode((DID_API_KEY + ':').encode()).decode()}",
        }

        # Randomly pick a voice + avatar
        chosen_guide = random.randint(0, 4)
        voice_id = guides[chosen_guide]
        image_file = images[chosen_guide]

        # === STEP 1: Upload an image directly to D-ID's /images endpoint ===
        with open(image_file, "rb") as f:
            files = {"image": (image_file, f, "image/jpeg")}
            upload_resp = requests.post("https://api.d-id.com/images", headers=headers, files=files)

        if upload_resp.status_code != 201:
            raise HTTPException(
                status_code=upload_resp.status_code,
                detail=f"Image upload failed: {upload_resp.text}"
            )

        source_url = upload_resp.json()["url"]
        print(f"✅ Image uploaded successfully: {source_url}")

        # === STEP 2: Create the talking avatar ===
        payload = {
            "source_url": source_url,
            "script": {
                "type": "text",
                "provider": {"type": "elevenlabs", "voice_id": voice_id},
                "input": request.text
            },
            "config": {"stitch": True, "align_driver": True}
        }

        talk_resp = requests.post("https://api.d-id.com/talks", headers=headers, json=payload)
        if talk_resp.status_code != 201:
            raise HTTPException(
                status_code=talk_resp.status_code,
                detail=f"Talk creation failed: {talk_resp.text}"
            )

        talk_id = talk_resp.json()["id"]
        print(f"🎬 Video generation started (talk_id={talk_id})")

        # === STEP 3: Poll for completion ===
        status_url = f"https://api.d-id.com/talks/{talk_id}"
        video_url = None
        while True:
            status_resp = requests.get(status_url, headers=headers)
            data = status_resp.json()
            if data.get("status") == "done":
                video_url = data["result_url"]
                break
            elif data.get("status") == "error":
                raise HTTPException(status_code=500, detail=f"D-ID error: {data}")
            time.sleep(3)

        print(f"✅ Video ready from D-ID: {video_url}")

        # === STEP 4: Download video bytes from D-ID ===
        video_resp = requests.get(video_url)
        if video_resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to download video from D-ID")

        video_bytes = video_resp.content

        # === STEP 5: Upload to S3 ===
        timestamp = int(time.time())
        s3_filename = f"avatars/avatar_{timestamp}.mp4"
        s3_url = upload_video_to_s3(video_bytes, s3_filename)
        print(f"✅ Uploaded to S3: {s3_url}")

        return {
            "message": "Avatar video created and uploaded successfully",
            "s3_url": s3_url,
            "voice_id": voice_id,
            "avatar_image": image_file
        }

    except Exception as e:
        print(f"Error in generate_talking_avatar: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

