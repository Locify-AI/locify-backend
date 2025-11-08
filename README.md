# Locify Backend API

A FastAPI backend service for Locify, a tour guide app that uses MCP (Model Context Protocol) agents to discover historical locations and generate immersive tour guide narrations.

## Features

- **Location Discovery**: Automatically discovers historical landmarks, museums, and cultural sites when users enter new cities/towns
- **MCP Agent Integration**: Uses Dedalus Labs MCP agents to interact with Foursquare Places API and web search
- **Narration Generation**: Generates 90-second immersive tour guide narrations for discovered locations
- **SQLite Database**: Stores all discovered locations and narrations locally
- **RESTful API**: Clean REST API for frontend integration

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required API keys:
- `DEDALUS_API_KEY`: Your Dedalus Labs API key

### 3. Run the Server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Discover Locations with Narrations

**POST** `/api/discover-locations`

Single endpoint that discovers historical locations (up to 20) and automatically generates narrations for each location. Returns name, coordinates, category, and narration for each location.

**Request Body:**
```json
{
  "latitude": 40.3487,
  "longitude": -74.6553,
  "radius": 1000,
  "user_id": "optional_user_id"
}
```

**Response:**
```json
{
  "message": "Discovered 10 locations with narrations",
  "locations": [
    {
      "name": "Princeton University Chapel",
      "latitude": 40.3487,
      "longitude": -74.6553,
      "category": "Historic Site",
      "narration": "You're standing at the Princeton University Chapel, a stunning Neo-Gothic masterpiece that has graced this campus since 1928. This magnificent structure..."
    },
    {
      "name": "Nassau Hall",
      "latitude": 40.3489,
      "longitude": -74.6588,
      "category": "Historic Building",
      "narration": "Welcome to Nassau Hall, the oldest building on Princeton's campus and a witness to over 250 years of American history..."
    }
    // ... up to 20 locations
  ]
}
```

**Features:**
- Automatically discovers up to 20 historical locations near the provided coordinates
- Generates immersive 90-second narrations for each location using AI research
- Returns only essential fields: `name`, `latitude`, `longitude`, `category`, and `narration`
- Caches results - if a city has been discovered before, returns existing locations with narrations
- Stores all data in SQLite database for future retrieval

## Database Schema

The application uses SQLite with three main tables:

1. **user_locations**: Tracks when users discover new cities/towns
2. **locations**: Stores discovered historical locations with details
3. **narrations**: Stores generated tour guide narrations for locations

## How It Works

1. **Location Discovery**: When a user provides coordinates, the system checks if they're in a new city (within 5km radius). If new, it calls the MCP agent to discover up to 20 historical locations using Foursquare Places API.

2. **JSON Parsing**: The MCP agent response is parsed to extract a JSON array of locations. The parser handles various response formats including markdown code blocks.

3. **Database Storage**: Discovered locations are stored in SQLite with details from Foursquare (name, coordinates, category, description, address, rating, distance, etc.).

4. **Automatic Narration Generation**: For each discovered location, the system automatically generates immersive 90-second narrations by researching each location using web search and AI storytelling. Narrations are stored in the database for future use.

5. **Response**: Returns only essential fields (name, latitude, longitude, category, narration) in a clean, simple format.

## Development

### Project Structure

```
locify-backend/
├── main.py              # FastAPI application and endpoints
├── database.py          # Database configuration
├── models.py            # SQLAlchemy models
├── agents.py            # MCP agent functions
├── services.py          # Business logic and database operations
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # This file
```

### Database Initialization

The database is automatically initialized on server startup. The SQLite database file (`locify.db`) will be created in the project root.

## Testing

### Quick Test with Python

1. Start the server:
```bash
python main.py
```

2. In another terminal, run the test script:
```bash
python test_api.py
```

### Test with curl

1. Start the server:
```bash
python main.py
```

2. Test health endpoint:
```bash
curl http://localhost:8000/health
```

3. Test discover locations endpoint:
```bash
curl -X POST http://localhost:8000/api/discover-locations \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 40.3487,
    "longitude": -74.6553,
    "radius": 1500
  }'
```

Or use the test script:
```bash
chmod +x test_curl.sh
./test_curl.sh
```

### Test with Python requests

```python
import requests

response = requests.post(
    "http://localhost:8000/api/discover-locations",
    json={
        "latitude": 40.3487,
        "longitude": -74.6553,
        "radius": 1500
    }
)

print(response.json())
```

### Expected Response Time

- **First request (new city)**: 2-5 minutes
  - Location discovery: ~30-60 seconds
  - Narration generation: ~10-20 seconds per location (up to 20 locations)
  
- **Subsequent requests (cached city)**: < 1 second
  - Returns cached locations and narrations from database

### Testing Notes

⚠️ **Important**: 
- Make sure your `.env` file has valid API keys:
  - `DEDALUS_API_KEY`
  - `OPENAI_API_KEY` (for GPT-4.1)
  - `ANTHROPIC_API_KEY` (for Claude)
- First request may take several minutes as it needs to discover locations and generate narrations
- Subsequent requests for the same city will be much faster (cached)

## License

MIT

