"""
Test script for CRUD endpoints

Tests the new endpoints for checking saved locations and narrations.
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_get_all_cities():
    """Test getting all discovered cities"""
    print("=" * 60)
    print("Test: GET /api/cities")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/api/cities")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Total cities: {data.get('total')}")

        for city in data.get('cities', []):
            print(f"\nCity: {city['city_name']}")
            print(f"  Locations: {city['location_count']}")
            print(f"  Discovered: {city['discovered_at']}")
            print(f"  Coordinates: ({city['latitude']}, {city['longitude']})")
    else:
        print(f"Error: {response.text}")
    print()


def test_get_locations_by_city(city_name: str):
    """Test getting all locations for a specific city"""
    print("=" * 60)
    print(f"Test: GET /api/cities/{city_name}/locations")
    print("=" * 60)

    # URL encode the city name
    import urllib.parse
    encoded_city = urllib.parse.quote(city_name)

    response = requests.get(f"{BASE_URL}/api/cities/{encoded_city}/locations")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"City: {data['city_name']}")
        print(f"Total locations: {data['total']}")

        for loc in data.get('locations', [])[:3]:  # Show first 3
            print(f"\nLocation: {loc['name']}")
            print(f"  Category: {loc['category']}")
            print(f"  Address: {loc['address']}")
            print(f"  Has Narration: {'Yes' if loc['narration'] else 'No'}")
            if loc['narration']:
                print(f"  Narration Preview: {loc['narration'][:100]}...")
                print(f"  Word Count: {loc['narration_word_count']}")

        if data['total'] > 3:
            print(f"\n... and {data['total'] - 3} more locations")
    else:
        print(f"Error: {response.text}")
    print()


def test_get_location_by_id(location_id: int):
    """Test getting a specific location by ID"""
    print("=" * 60)
    print(f"Test: GET /api/locations/{location_id}")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/api/locations/{location_id}")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        loc = response.json()
        print(f"Location: {loc['name']}")
        print(f"Category: {loc['category']}")
        print(f"Coordinates: ({loc['latitude']}, {loc['longitude']})")
        print(f"Address: {loc['address']}")
        print(f"Rating: {loc['rating']}")
        print(f"Description: {loc['description']}")

        if loc['narration']:
            print(f"\nNarration ({loc['narration_word_count']} words):")
            print(loc['narration'])
        else:
            print("\nNo narration available")
    else:
        print(f"Error: {response.text}")
    print()


def test_get_all_locations():
    """Test getting all locations with pagination"""
    print("=" * 60)
    print("Test: GET /api/locations?limit=5")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/api/locations?limit=5")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Total locations in DB: {data['total']}")
        print(f"Showing: {len(data['locations'])} (skip={data['skip']}, limit={data['limit']})")

        for loc in data['locations']:
            print(f"\n- {loc['name']} ({loc['category']})")
            print(f"  Has narration: {loc['has_narration']}")
            print(f"  Created: {loc['created_at']}")
    else:
        print(f"Error: {response.text}")
    print()


def test_delete_location(location_id: int):
    """Test deleting a specific location"""
    print("=" * 60)
    print(f"Test: DELETE /api/locations/{location_id}")
    print("=" * 60)

    response = requests.delete(f"{BASE_URL}/api/locations/{location_id}")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print(f"Success: {response.json()['message']}")
    else:
        print(f"Error: {response.text}")
    print()


def test_delete_city(city_name: str):
    """Test deleting a city and all its locations"""
    print("=" * 60)
    print(f"Test: DELETE /api/cities/{city_name}")
    print("=" * 60)

    # URL encode the city name
    import urllib.parse
    encoded_city = urllib.parse.quote(city_name)

    response = requests.delete(f"{BASE_URL}/api/cities/{encoded_city}")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print(f"Success: {response.json()['message']}")
    else:
        print(f"Error: {response.text}")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Locify CRUD API Test Suite")
    print("=" * 60)
    print()

    # Test 1: Get all cities
    test_get_all_cities()

    # Test 2: Get all locations (paginated)
    test_get_all_locations()

    # Get the first city name from the cities list to use in subsequent tests
    cities_response = requests.get(f"{BASE_URL}/api/cities")
    if cities_response.status_code == 200:
        cities = cities_response.json().get('cities', [])

        if len(cities) > 0:
            first_city = cities[0]['city_name']

            # Test 3: Get locations for a specific city
            test_get_locations_by_city(first_city)

            # Get the first location ID to test individual location endpoint
            city_locations_response = requests.get(
                f"{BASE_URL}/api/cities/{first_city}/locations"
            )
            if city_locations_response.status_code == 200:
                locations = city_locations_response.json().get('locations', [])

                if len(locations) > 0:
                    first_location_id = locations[0]['id']

                    # Test 4: Get a specific location by ID
                    test_get_location_by_id(first_location_id)
        else:
            print("⚠️  No cities found in database.")
            print("   Run a discover-locations request first to populate the database.")

    print("\n" + "=" * 60)
    print("CRUD Tests Complete!")
    print("=" * 60)
    print("\nNote: Delete tests are commented out to prevent accidental data loss.")
    print("To test deletion, uncomment the following lines and run again:")
    print("  # test_delete_location(location_id)")
    print("  # test_delete_city(city_name)")
    print()
