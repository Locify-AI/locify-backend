import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner
from dotenv import load_dotenv
import json
import re

load_dotenv()


async def discover_historical_locations(latitude: float, longitude: float, radius: int = 2000):
    """
    Agent 1: Discovers historical landmarks, museums, monuments, and cultural sites
    near the user's location using Foursquare Places API.

    Args:
        latitude: User's current latitude
        longitude: User's current longitude
        radius: Search radius in meters (default: 2000m = 2km)

    Returns:
        JSON string containing list of historical/tourist POIs with details
    """
    client = AsyncDedalus()
    runner = DedalusRunner(client)

    ll_string = f"{latitude},{longitude}"

    result = await runner.run(
        input=f"""You are a location discovery specialist for Locify, a tour guide app.

        **YOUR MISSION:** Find diverse historical landmarks, museums, monuments, and cultural sites
        within {radius} meters of coordinates: {ll_string}

        **STEP 1: DISCOVER DIVERSE LOCATIONS**
        CRITICAL: You MUST find 8 locations and return a diverse mix of location types.
        Do NOT return only fountains, only museums, or only one type.

        Use Foursquare Places API to discover locations:

        1. Use search_near_point() to search for these broader categories (3-5 searches total):
           - "historic site" (this will find monuments, landmarks, historic buildings)
           - "museum" (art, history, science museums)
           - "church OR cathedral" (religious historic buildings)
           - "theater OR cultural center" (cultural venues)

        2. Combine results from searches - aim for 20-30+ results before filtering

        3. Filter to ensure diversity BUT KEEP 8 LOCATIONS - select a mix of:
           - Museums (art, history, science)
           - Historic buildings (churches, cathedrals, libraries)
           - Monuments and memorials
           - Historic university buildings
           - Cultural centers (theaters, opera houses)
           - Government buildings (if historically significant)
           - Historic parks and gardens

        4. SIMPLIFIED FILTERING RULES (be LESS strict to keep more locations):
           - Avoid having MORE THAN 3 of the same type (e.g., max 3 fountains, max 3 churches)
           - Prioritize unique, one-of-a-kind locations but still include interesting common types
           - Include places with history, cultural importance, or architectural interest
           - Aim for variety but DO NOT over-filter - better to have 8 locations than 2

        5. MINIMUM REQUIREMENT: Return 8 locations

        6. Sort by a balance of distance and significance

        **REQUIRED OUTPUT FORMAT - Return a structured JSON array:**
        ```json
        [
          {{
            "name": "Place name",
            "fsq_id": "Foursquare place ID (if available)",
            "coordinates": {{
              "latitude": 40.123,
              "longitude": -74.456
            }},
            "category": "Primary category",
            "distance": "Distance from user in meters (if available)",
            "address": "Full address (if available)",
            "rating": "Rating out of 10 (if available)",
            "description": "Brief description from Foursquare (if available)",
            "popularity": "Number of tips/reviews (if available)",
            "historical_significance": "Why this place is historically/culturally important (brief)"
          }}
        ]
        ```

        **CRITICAL REQUIREMENTS:**
        - Return ONLY the JSON array with no additional commentary
        - You MUST return 8 locations
        - You MUST return a DIVERSE mix of location types
        - DO NOT return only fountains, only museums, or only one category
        - Prioritize places with historical, cultural, or architectural significance
        - Filter out generic restaurants, cafes, shops unless historically significant
        - Include all available details from Foursquare (rating, popularity, etc.)

        **EXECUTION ORDER:**
        1. Perform 3-5 search queries (historic site, museum, church, theater)
        2. You should have 20-30+ location results after all searches
        3. Filter and select 8 locations with the most diverse mix
        4. Return the complete JSON array
        5. VERIFY before returning: Do you have at least 8 locations in your JSON array?

        Begin by discovering diverse locations, then return the JSON.""",

        model=["openai/gpt-4.1"],  # GPT-4.1 for structured data extraction

        mcp_servers=[
            "windsor/foursquare-places-mcp"  # Foursquare for location discovery
        ],

    )

    print("\n" + "="*80)
    print("LOCATION DISCOVERY AGENT - STREAMING RESULTS:")
    print("="*80)

    # Stream the discovery process
    full_output = result.final_output

    print("\n" + "="*80)
    print(f"Response length: {len(full_output)} characters")
    print("="*80 + "\n")

    # Debug: Try to parse and count locations from the response
    try:
        import re

        # Try to extract JSON array
        response_text = full_output.strip()

        # Look for JSON array in response
        json_match = re.search(r'\[[\s\S]*\]', response_text)
        if json_match:
            try:
                locations = json.loads(json_match.group(0))
                print(f"DEBUG: Successfully parsed {len(locations)} locations from agent 1")
                for i, loc in enumerate(locations):
                    print(f"  Location {i+1}: {loc.get('name', 'Unknown')} - {loc.get('category', 'No category')}")
            except json.JSONDecodeError as e:
                print(f"DEBUG: Failed to parse JSON - {str(e)}")
                print(f"DEBUG: First 500 chars of extracted JSON: {json_match.group(0)[:500]}")
        else:
            print("DEBUG: No JSON array pattern found in response")
            print(f"DEBUG: First 500 chars of response: {response_text[:500]}")

    except Exception as e:
        print(f"DEBUG: Error during debug parsing - {str(e)}")

    print("="*80 + "\n")

    return full_output


async def generate_tour_guide_narration(
    place_name: str,
    place_category: str,
    coordinates: dict,
    address: str = "",
    foursquare_description: str = "",
    historical_significance: str = ""
):
    """
    Agent 2: Generates immersive 60-second audio tour guide narration by researching
    the location using web search and synthesizing historical/cultural information.

    Args:
        place_name: Name of the landmark/POI
        place_category: Category (e.g., "Historic Site", "Museum", "Monument")
        coordinates: Dict with latitude and longitude
        address: Full address of the location
        foursquare_description: Optional description from Foursquare
        historical_significance: Brief note on historical significance

    Returns:
        60-second narration script ready for text-to-speech conversion (plain text)
        Return only the narration text without any other text or formatting, or introduction or conclusion.
    """
    client = AsyncDedalus()
    runner = DedalusRunner(client)

    lat = coordinates.get('latitude', 0)
    lon = coordinates.get('longitude', 0)

    try:
        result = await runner.run(
            input=f"""You are an expert AI tour guide for Locify.
                Your ONLY task is to narrate about a single location exactly as if you were speaking to a traveler.

                **LOCATION:**
                - Name: {place_name}
                - Category: {place_category}
                - Address: {address}
                - Coordinates: {lat}, {lon}
                - Foursquare Description: {foursquare_description}
                - Historical Significance: {historical_significance}

                **CRITICAL OUTPUT REQUIREMENTS:**
                - You MUST return a single JSON object.
                - It MUST have only one field: `"narration"`.
                - The narration must be written exactly as a spoken tour guide would talk:
                - Begin immediately with information (e.g., “This historic site was built in 1882…” or “Welcome to…”)
                - Do NOT say things like “I will now research…” or “Here’s what I found.”
                - Do NOT use filler words or meta-commentary.
                - Do NOT describe your process.
                - Keep the narration between 150–200 words, written in natural spoken tone.
                - NO markdown, code blocks, or extra text outside JSON.

                **Example valid output:**
                ```json
                {{ "narration": "This historic cathedral, completed in 1890, stands as..." }}""",

            model=["anthropic/claude-sonnet-4-20250514"],  # Claude for creative storytelling
            # model=["openai/gpt-4.1"],  # GPT-4.1 for structured data extraction

            mcp_servers=[
                "tsion/brave-search-mcp",  # Web search for historical info
                # "akakak/sonar"
                # "joerup/exa-mcp"          
            ],
        )

        # Get narration result
        print("\n" + "-"*80)
        print(f"🎙️  GENERATING NARRATION FOR: {place_name}")
        print("-"*80 + "\n")

        full_narration = result.final_output

                # ✅ MODIFIED SECTION START — strict JSON parse / cleanup
        if not full_narration:
            print(f"⚠️  WARNING: No narration generated for {place_name}")
            return ""

        # Try to extract the narration JSON safely
        try:
            match = re.search(r"\{[\s\S]*\}", full_narration)
            if match:
                parsed = json.loads(match.group(0))
                narration_text = parsed.get("narration", "").strip()
            else:
                # fallback if model ignored JSON
                narration_text = full_narration.strip()
        except Exception as e:
            print(f"⚠️  JSON parse failed for narration ({place_name}): {str(e)}")
            narration_text = re.sub(
                r"(?i)(i('| a)?ll|here('| i)?s|now|let('| )?s|as an ai).*", "", 
                full_narration
            ).strip()

        # Remove any leading meta sentences like “I’ll conduct…” etc.
        narration_text = re.sub(
            r"(?i)^(i('| )?(will|shall|am)|here('| )?is|let('| )?me|as an ai|sure,|okay,).*?:?\s*", 
            "", 
            narration_text
        ).strip()

        print(f"🧭 Final narration (cleaned): {narration_text[:120]}...")
        return narration_text
        # ✅ MODIFIED SECTION END — strict JSON parse / cleanup



    except Exception as e:
        print(f"❌ ERROR generating narration for {place_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return ""


async def discover_locations_with_narrations(latitude: float, longitude: float, radius: int = 2000):
    """
    Combined workflow: Discovers locations (Agent 1) and generates narrations (Agent 2).
    This function orchestrates both agents in sequence with streaming.

    Args:
        latitude: User's current latitude
        longitude: User's current longitude
        radius: Search radius in meters (default: 2000m = 2km)

    Returns:
        JSON string with locations and their narrations
    """
    print("\n" + "="*80)
    print("🚀 STARTING TWO-AGENT WORKFLOW")
    print("="*80 + "\n")

    # AGENT 1: Discover locations
    print("📍 AGENT 1: Discovering historical locations...")
    locations_json = await discover_historical_locations(latitude, longitude, radius)

    # Parse locations
    json_match = re.search(r'\[[\s\S]*\]', locations_json)
    if not json_match:
        print("❌ ERROR: Could not parse locations from Agent 1")
        return "[]"

    try:
        locations = json.loads(json_match.group(0))
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Failed to parse JSON - {str(e)}")
        return "[]"

    if not locations or len(locations) == 0:
        print("❌ ERROR: No locations discovered")
        return "[]"

    print(f"\n✅ Agent 1 complete: Found {len(locations)} locations")

    # AGENT 2: Generate narrations for each location using async/await with batching
    print(f"\n📝 AGENT 2: Generating narrations for {len(locations)} locations using async batches...")
    print("="*80 + "\n")

    async def generate_with_error_handling(location, index):
        """Async function to generate narration with error handling"""
        print(f"[{index}/{len(locations)}] Starting: {location.get('name', 'Unknown')}")

        try:
            narration = await generate_tour_guide_narration(
                place_name=location.get('name', 'Unknown'),
                place_category=location.get('category', 'Unknown'),
                coordinates=location.get('coordinates', {}),
                address=location.get('address', ''),
                foursquare_description=location.get('description', ''),
                historical_significance=location.get('historical_significance', '')
            )

            # Add narration to location object
            location['narration'] = narration
            print(f"✅ [{index}/{len(locations)}] Complete: {location.get('name', 'Unknown')} ({len(narration) if narration else 0} chars)")
            return location

        except Exception as e:
            print(f"⚠️  [{index}/{len(locations)}] ERROR for {location.get('name', 'Unknown')}: {str(e)}")
            import traceback
            traceback.print_exc()
            # Still add location but with empty narration
            location['narration'] = None
            return location

    # Process in batches to avoid overwhelming MCP servers
    BATCH_SIZE = 1
    locations_with_narrations = []
    
    # Delay between batches (in seconds) to avoid rate limiting
    DELAY_BETWEEN_BATCHES = 2.0  # 2 seconds between batches
    DELAY_BETWEEN_LOCATIONS = 1.0  # 1 second between individual locations (if BATCH_SIZE = 1)

    for i in range(0, len(locations), BATCH_SIZE):
        batch = locations[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(locations) + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"\n🔄 Processing Batch {batch_num}/{total_batches} ({len(batch)} locations)")
        print("-" * 80)

        # If processing one at a time, add delay between locations
        if BATCH_SIZE == 1:
            # Process single location
            result = await generate_with_error_handling(batch[0], i + 1)
            locations_with_narrations.append(result)
            
            # Add delay after each location (except the last one)
            if i + BATCH_SIZE < len(locations):
                print(f"⏳ Waiting {DELAY_BETWEEN_LOCATIONS}s before next location...")
                await asyncio.sleep(DELAY_BETWEEN_LOCATIONS)
        else:
            # Process batch concurrently
            # Create tasks for this batch
            tasks = [
                generate_with_error_handling(location, i + idx + 1)
                for idx, location in enumerate(batch)
            ]

            # Execute batch concurrently using asyncio.gather
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            for idx, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    # Get the original location from the batch
                    failed_location = batch[idx].copy()
                    failed_location['narration'] = None
                    print(f"⚠️  Exception in batch for {failed_location.get('name', 'Unknown')}: {str(result)}")
                    locations_with_narrations.append(failed_location)
                else:
                    locations_with_narrations.append(result)
            
            # Add delay between batches (except after the last batch)
            if i + BATCH_SIZE < len(locations):
                print(f"⏳ Waiting {DELAY_BETWEEN_BATCHES}s before next batch...")
                await asyncio.sleep(DELAY_BETWEEN_BATCHES)

        print(f"✅ Batch {batch_num}/{total_batches} complete\n")

    print("\n" + "="*80)
    print(f"✅ TWO-AGENT WORKFLOW COMPLETE")
    print(f"   Total locations: {len(locations_with_narrations)}")
    print(f"   With narrations: {sum(1 for loc in locations_with_narrations if loc.get('narration'))}")
    print("="*80 + "\n")

    for i, location in enumerate(locations_with_narrations):
        print(f"[{i+1}/{len(locations_with_narrations)}] Location: {location.get('name', 'Unknown')}")
        print(f"   Narration: {location.get('narration', 'No narration')}")
        print("="*80 + "\n")

    # Return as JSON string
    return json.dumps(locations_with_narrations, indent=2)
