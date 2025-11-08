import asyncio
from dedalus_labs import AsyncDedalus, DedalusRunner
from dedalus_labs.utils.streaming import stream_async
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
        CRITICAL: You MUST find 10 locations and return a diverse mix of location types.
        Do NOT return only fountains, only museums, or only one type.

        Use Foursquare Places API to discover locations:

        1. Use search_near_point() to search for these broader categories (3-5 searches total):
           - "historic site" (this will find monuments, landmarks, historic buildings)
           - "museum" (art, history, science museums)
           - "church OR cathedral" (religious historic buildings)
           - "theater OR cultural center" (cultural venues)

        2. Combine results from searches - aim for 20-30+ results before filtering

        3. Filter to ensure diversity BUT KEEP 10 LOCATIONS - select a mix of:
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
           - Aim for variety but DO NOT over-filter - better to have 10 locations than 2

        5. MINIMUM REQUIREMENT: Return 10 locations

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
        - You MUST return 10 locations
        - You MUST return a DIVERSE mix of location types
        - DO NOT return only fountains, only museums, or only one category
        - Prioritize places with historical, cultural, or architectural significance
        - Filter out generic restaurants, cafes, shops unless historically significant
        - Include all available details from Foursquare (rating, popularity, etc.)

        **EXECUTION ORDER:**
        1. Perform 3-5 search queries (historic site, museum, church, theater)
        2. You should have 20-30+ location results after all searches
        3. Filter and select 10 locations with the most diverse mix
        4. Return the complete JSON array
        5. VERIFY before returning: Do you have at least 10 locations in your JSON array?

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
            input=f"""You are a master storyteller and tour guide researcher for Locify.

        **LOCATION TO RESEARCH:**
        - Name: {place_name}
        - Category: {place_category}
        - Address: {address}
        - Coordinates: {lat}, {lon}
        - Foursquare Description: {foursquare_description}
        - Historical Significance: {historical_significance}

        **YOUR RESEARCH MISSION:**
        Conduct comprehensive research to uncover the fascinating story of this location.
        Use ALL available tools to search for:

        **1. HISTORICAL DEPTH (Priority: High)**
        - Construction/founding date and architect/founder
        - Original purpose and how it has evolved
        - Key historical events that occurred here
        - Architectural style and unique design features
        - Notable people associated with the location
        - Awards, recognitions, or records it holds

        **2. CULTURAL SIGNIFICANCE (Priority: High)**
        - Role in local/national culture or history
        - Appearances in films, books, art, or media
        - Impact on surrounding community or society
        - Legends, folklore, or famous anecdotes
        - Current cultural programs or significance

        **3. HIDDEN GEMS & INSIDER DETAILS (Priority: Medium)**
        - Architectural secrets or details most people miss
        - Surprising facts or statistics
        - Best times to visit or unique experiences
        - Recent renovations or changes
        - What locals love most about this place

        **4. VISUAL & SENSORY DETAILS (Priority: Medium)**
        - Striking visual features visitors should notice
        - Seasonal variations or atmospheric qualities
        - Unique sounds, materials, or artistic elements

        **RESEARCH STRATEGY:**
        - Search web for: "{place_name} history"
        - Search web for: "{place_name} architecture facts"
        - Search web for: "{place_name} cultural significance"
        - Search web for: "{place_name} visitor guide hidden details"
        - Look for academic sources, historical archives, and heritage site records
        - Find recent news articles or cultural reviews (past 2 years)

        **AFTER COMPLETING YOUR RESEARCH:**

        Write a captivating 60-second spoken narration (150-200 words) using this structure:

        ---

        **[HOOK - 10 seconds / 30-40 words]**
        Open with a surprising fact, vivid image, or compelling question.
        Create immediate presence with "You're standing at..." or "Welcome to..."
        Make listeners want to know more.

        **[HISTORICAL CONTEXT - 20 seconds / 50-60 words]**
        Share the origin story with specific dates, names, and architectural details.
        Explain why this location is historically or culturally significant.
        Connect it to broader historical movements or events.

        **[FASCINATING DETAILS - 20 seconds / 50-60 words]**
        Reveal 2-3 unexpected facts or hidden gems from your research.
        Include authentic anecdotes, famous visitors, or architectural secrets.
        Make listeners see the location with fresh eyes.

        **[CONTEMPORARY RELEVANCE - 10 seconds / 30-40 words]**
        Connect past to present—how is it used today?
        End with an invitation to explore or observe something specific.
        Leave listeners feeling enriched and curious.

        ---

        **NARRATION TONE REQUIREMENTS:**
        - Conversational and warm (like a knowledgeable friend)
        - Enthusiastic but not overwhelming
        - Use accessible language—no academic jargon
        - Create personal connection with "you" and "imagine"
        - Write for spoken delivery with natural pauses
        - Vary sentence length for rhythm and emphasis

        **STRICT RULES:**
        ❌ NO generic descriptions that could apply anywhere
        ❌ NO lists of amenities (WiFi, parking) unless historically relevant
        ❌ NO academic citations or footnote references
        ❌ NO apologetic language ("Unfortunately, I don't have...")
        ❌ NO overly long sentences that are hard to follow when spoken

        ✅ DO use specific dates, names, and historical facts
        ✅ DO paint vivid sensory pictures
        ✅ DO connect past to present meaningfully
        ✅ DO end with actionable invitation to explore

        **OUTPUT FORMAT:**
        Provide your final 60-second narration script ONLY.
        Do NOT include research notes or sources in the final output.
        The script should be ready to send directly to ElevenLabs for audio generation.
        Do not include any other text or formatting (only the narration script), or introduction or conclusion like "Here is the narration for..." or "Now I have comprehensive information about...".

        Write the narration now, focusing on information discovered in your research.""",

            model=["anthropic/claude-sonnet-4-20250514"],  # Claude for creative storytelling

            mcp_servers=[
                "tsion/brave-search-mcp",  # Web search for historical info
                # "joerup/exa-mcp"           # Semantic search for academic sources
            ],
        )

        # Get narration result
        print("\n" + "-"*80)
        print(f"🎙️  GENERATING NARRATION FOR: {place_name}")
        print("-"*80 + "\n")

        full_narration = result.final_output

        if not full_narration:
            print(f"⚠️  WARNING: No narration generated for {place_name}")
            return ""

        print("-"*80 + "\n")

        return full_narration

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

    # AGENT 2: Generate narrations for each location IN BATCHES OF 3
    print(f"\n📝 AGENT 2: Generating narrations for {len(locations)} locations IN BATCHES OF 3...")
    print("="*80 + "\n")

    # Create tasks for parallel execution
    async def generate_with_error_handling(location, index):
        """Helper function to generate narration with error handling"""
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
            print(f"✅ [{index}/{len(locations)}] Complete: {location.get('name', 'Unknown')} ({len(narration)} chars)")
            return location

        except Exception as e:
            print(f"⚠️  [{index}/{len(locations)}] ERROR for {location.get('name', 'Unknown')}: {str(e)}")
            # Still add location but with empty narration
            location['narration'] = None
            return location

    # Process in batches of 5 to avoid overwhelming MCP servers
    BATCH_SIZE = 5
    locations_with_narrations = []

    for i in range(0, len(locations), BATCH_SIZE):
        batch = locations[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(locations) + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"\n🔄 Processing Batch {batch_num}/{total_batches} ({len(batch)} locations)")
        print("-" * 80)

        # Create tasks for this batch
        tasks = [
            generate_with_error_handling(location, i + idx + 1)
            for idx, location in enumerate(batch)
        ]

        # Execute batch in parallel
        batch_results = await asyncio.gather(*tasks)
        locations_with_narrations.extend(batch_results)

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
