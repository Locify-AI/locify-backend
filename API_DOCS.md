# Locify Backend API Documentation

## Discovery Endpoint Response Format

### POST `/api/discover-locations`

**Response includes location IDs for frontend retrieval:**

```json
{
  "message": "Discovered 10 locations with narrations",
  "locations": [
    {
      "id": 1,
      "name": "Princeton University Chapel",
      "latitude": 40.3487,
      "longitude": -74.6553,
      "category": "Historic Building",
      "narration": "You're standing at one of the most beautiful collegiate chapels...",
      "fsq_id": "4b7f3a...",
      "address": "Princeton University, Princeton, NJ 08544",
      "description": "Neo-Gothic chapel completed in 1928"
    },
    {
      "id": 2,
      "name": "Nassau Hall",
      "latitude": 40.3485,
      "longitude": -74.6590,
      "category": "Historic Building",
      "narration": "Welcome to Nassau Hall, the oldest building...",
      "fsq_id": "4b8d2b...",
      "address": "Princeton University, Princeton, NJ 08544",
      "description": "Built in 1756, served as US Capitol in 1783"
    }
  ]
}
```

## Frontend Usage

### 1. Initial Discovery Request
```javascript
// User opens app at their location
const response = await fetch('http://localhost:8000/api/discover-locations', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    latitude: 40.3487,
    longitude: -74.6553,
    radius: 2000
  })
});

const data = await response.json();

// Save location IDs for later retrieval
const locationIds = data.locations.map(loc => loc.id);
localStorage.setItem('nearbyLocationIds', JSON.stringify(locationIds));

// Display locations on map
data.locations.forEach(location => {
  addMarkerToMap(location.id, location.name, location.latitude, location.longitude);
});
```

### 2. Retrieve Specific Location Later
```javascript
// User taps on a marker or wants to replay narration
const locationId = 5;

const response = await fetch(`http://localhost:8000/api/locations/${locationId}`);
const location = await response.json();

// Play the narration
playAudio(location.narration);

// Show details
showLocationDetails(location);
```

### 3. Cache Management
```javascript
// Check what cities are already cached
const response = await fetch('http://localhost:8000/api/cities');
const cities = await response.json();

// Show user their discovery history
cities.cities.forEach(city => {
  console.log(`${city.city_name}: ${city.location_count} locations`);
});
```

## Key Benefits for Frontend

✅ **Persistent IDs**: Each location has a stable database ID
✅ **Easy Retrieval**: Use `GET /api/locations/{id}` anytime
✅ **No Duplication**: Same location always has same ID
✅ **Offline-Ready**: Store IDs locally, fetch details when online

## Example Mobile App Flow

```
1. User opens app
   ↓
2. POST /api/discover-locations → Returns 10 locations with IDs
   ↓
3. Store IDs: [1, 2, 3, 4, 5, ...]
   ↓
4. User walks to location #3
   ↓
5. GET /api/locations/3 → Fetch full details + narration
   ↓
6. Play narration audio
```

## Response Fields Explained

| Field | Type | Description | Usage |
|-------|------|-------------|-------|
| `id` | int | **Database ID** (use this for retrieval) | Store for later fetching |
| `name` | string | Location name | Display to user |
| `latitude` | float | Coordinates | Map marker |
| `longitude` | float | Coordinates | Map marker |
| `category` | string | Location type | Filter/sort |
| `narration` | string | 90-second script | Text-to-speech |
| `fsq_id` | string | Foursquare ID | Link to Foursquare |
| `address` | string | Full address | Directions |
| `description` | string | Brief description | Preview text |

## Complete Endpoint List

### Discovery
- `POST /api/discover-locations` - Discover nearby locations with narrations

### Retrieval (use the IDs from discovery response)
- `GET /api/locations/{id}` - Get specific location by ID
- `GET /api/locations` - Get all locations (paginated)
- `GET /api/cities` - Get all cached cities
- `GET /api/cities/{city_name}/locations` - Get all locations in a city

### Management
- `DELETE /api/locations/{id}` - Delete location
- `DELETE /api/cities/{city_name}` - Delete city + all locations

## Testing

```bash
# Discover locations and get IDs
curl -X POST http://localhost:8000/api/discover-locations \
  -H "Content-Type: application/json" \
  -d '{"latitude": 40.3487, "longitude": -74.6553, "radius": 2000}'

# Response will include IDs like: {"locations": [{"id": 1, ...}, {"id": 2, ...}]}

# Retrieve specific location by ID
curl http://localhost:8000/api/locations/1
```
