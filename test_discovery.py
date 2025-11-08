"""
Test script for discovery endpoint with ID retrieval

This demonstrates how the frontend should use location IDs
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_discover_and_retrieve():
    """Test discovering locations and retrieving by ID"""
    print("=" * 80)
    print("TEST: Discovery + ID Retrieval Flow")
    print("=" * 80)
    print()

    # Step 1: Discover locations
    print("Step 1: Discovering locations near Princeton University...")
    print("-" * 80)

    discover_payload = {
        "latitude": 40.3487,
        "longitude": -74.6553,
        "radius": 2000
    }

    response = requests.post(
        f"{BASE_URL}/api/discover-locations",
        json=discover_payload,
        timeout=300
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return

    data = response.json()
    print(f"✅ {data['message']}")
    print()

    # Step 2: Show locations with IDs
    print("Step 2: Locations discovered (with IDs for retrieval):")
    print("-" * 80)

    locations = data.get('locations', [])
    location_ids = []

    for i, loc in enumerate(locations, 1):
        location_id = loc.get('id')
        location_ids.append(location_id)

        print(f"\n[{i}] {loc.get('name')}")
        print(f"    🆔 ID: {location_id} ⭐ (save this for later retrieval)")
        print(f"    📍 Category: {loc.get('category', 'N/A')}")
        print(f"    📌 Coordinates: ({loc.get('latitude')}, {loc.get('longitude')})")
        print(f"    🏠 Address: {loc.get('address', 'N/A')}")

        if loc.get('fsq_id'):
            print(f"    🔗 Foursquare ID: {loc.get('fsq_id')}")

        narration = loc.get('narration', '')
        word_count = len(narration.split())
        print(f"    📝 Narration: {word_count} words")
        print(f"       Preview: {narration[:100]}...")

    print()
    print("=" * 80)
    print(f"✅ Total locations discovered: {len(locations)}")
    print(f"📋 Location IDs: {location_ids}")
    print("=" * 80)
    print()

    # Step 3: Demonstrate retrieval by ID
    if len(location_ids) > 0:
        print("Step 3: Retrieving location details by ID...")
        print("-" * 80)

        # Pick the first location
        first_id = location_ids[0]
        print(f"Fetching details for location ID: {first_id}")
        print()

        detail_response = requests.get(f"{BASE_URL}/api/locations/{first_id}")

        if detail_response.status_code == 200:
            loc_detail = detail_response.json()

            print(f"✅ Retrieved: {loc_detail['name']}")
            print(f"   ID: {loc_detail['id']}")
            print(f"   Category: {loc_detail['category']}")
            print(f"   Address: {loc_detail['address']}")
            print(f"   Description: {loc_detail['description']}")
            print(f"   Coordinates: ({loc_detail['latitude']}, {loc_detail['longitude']})")
            print(f"   Rating: {loc_detail.get('rating', 'N/A')}")
            print(f"   Created: {loc_detail['created_at']}")
            print()
            print("   Full Narration:")
            print("   " + "-" * 76)
            print(f"   {loc_detail['narration']}")
            print("   " + "-" * 76)
        else:
            print(f"❌ Error fetching location: {detail_response.text}")

        print()

    # Step 4: Show frontend integration example
    print("=" * 80)
    print("Step 4: Frontend Integration Example")
    print("=" * 80)
    print()
    print("JavaScript code to integrate in your frontend:")
    print()
    print("```javascript")
    print("// 1. Discover locations")
    print("const response = await fetch('http://localhost:8000/api/discover-locations', {")
    print("  method: 'POST',")
    print("  headers: { 'Content-Type': 'application/json' },")
    print("  body: JSON.stringify({")
    print("    latitude: 40.3487,")
    print("    longitude: -74.6553,")
    print("    radius: 2000")
    print("  })")
    print("});")
    print()
    print("const data = await response.json();")
    print()
    print("// 2. Save location IDs")
    print("const locationIds = data.locations.map(loc => loc.id);")
    print(f"// Example IDs: {location_ids[:3]} ...")
    print()
    print("// 3. Later: Retrieve specific location by ID")
    if len(location_ids) > 0:
        print(f"const locationId = {location_ids[0]};")
    print("const detailResponse = await fetch(`http://localhost:8000/api/locations/${locationId}`);")
    print("const locationDetail = await detailResponse.json();")
    print()
    print("// 4. Use the narration")
    print("playNarrationAudio(locationDetail.narration);")
    print("```")
    print()


if __name__ == "__main__":
    print()
    print("=" * 80)
    print("Locify Discovery + ID Retrieval Test")
    print("=" * 80)
    print()
    print("This test demonstrates:")
    print("1. Discovering locations via POST /api/discover-locations")
    print("2. Receiving location IDs in the response")
    print("3. Using those IDs to retrieve location details later")
    print()
    print("⚠️  Note: First request may take 2-5 minutes")
    print("   (Agent discovers locations + generates narrations in parallel)")
    print()
    input("Press Enter to start test...")
    print()

    test_discover_and_retrieve()

    print()
    print("=" * 80)
    print("✅ Test Complete!")
    print("=" * 80)
    print()
