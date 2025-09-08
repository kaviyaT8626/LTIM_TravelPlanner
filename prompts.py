def create_travel_prompt(prompt, vehicle_type=None, num_people=2, budget="Moderate"):
    """
    Create enhanced prompt for travel planning
    """
    return f"""
    You are an expert travel planner with extensive knowledge of routes across India. 
    Analyze this travel request: "{prompt}"
    
    Extract the following information:
    1. Start location
    2. End location 
    3. Types of stops requested (temples, hotels, fuel stations, restaurants, parks, etc.)
    4. Any specific preferences mentioned
    
    Then suggest appropriate stops between the start and end locations.
    
    For each stop, provide:
    - Name
    - Type (temple, hotel, fuel, restaurant, park, viewpoint, shopping, etc.)
    - Coordinates (latitude,longitude) - make them realistic for the route
    - Brief description (1-2 sentences)
    - Estimated visiting time (in hours)
    - Rating (out of 5)
    
    Also provide:
    - Estimated total driving distance
    - Estimated total driving time (excluding visiting time)
    - Estimated total visiting time at all stops
    - Estimated total trip time (driving + visiting)
    - Vehicle suggestion based on the route, number of people ({num_people}), and terrain
    
    Return your response as JSON with this structure:
    {{
        "start": "start_location",
        "end": "end_location",
        "total_driving_distance": "estimated_distance",
        "total_driving_time": "estimated_driving_time",
        "total_visiting_time": "estimated_visiting_time",
        "total_trip_time": "estimated_total_time",
        "vehicle_suggestion": "appropriate_vehicle",
        "stops": [
            {{
                "name": "stop_name",
                "type": "stop_type", 
                "coordinates": "lat,lng",
                "description": "brief_description",
                "visiting_time": "x.x",
                "rating": "x.x"
            }},
            ...
        ],
        "additional_recommendations": "extra_tips_and_suggestions"
    }}
    
    Only return the JSON object, no additional text.
    Make the suggestions realistic and practical for {num_people} people with a {budget} budget.
    """