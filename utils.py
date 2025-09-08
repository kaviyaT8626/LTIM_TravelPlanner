import google.generativeai as genai
from math import radians, sin, cos, sqrt, atan2
import re

def get_available_models(api_key):
    """Get list of available models"""
    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        return [model.name for model in models]
    except Exception as e:
        return []

def find_best_model(api_key):
    """Find the best available model for content generation"""
    try:
        models = get_available_models(api_key)
        
        # Preferred models in order of preference
        preferred_models = [
            "models/gemini-pro",
            "models/gemini-1.0-pro",
            "models/gemini-1.5-pro",
            "models/text-bison-001",
            "models/chat-bison-001"
        ]
        
        for model in preferred_models:
            if model in models:
                return model
                
        # If no preferred models found, return the first available model
        if models:
            return models[0]
            
        return None
    except Exception as e:
        return None

def calculate_travel_time(start_coords, end_coords, vehicle_type="Car"):
    """Calculate approximate travel time between two coordinates"""
    try:
        if not start_coords or not end_coords:
            return 0
            
        # Validate coordinates first
        if not validate_coordinates(start_coords) or not validate_coordinates(end_coords):
            return 1.5  # Default fallback
            
        lat1, lon1 = map(float, start_coords.split(','))
        lat2, lon2 = map(float, end_coords.split(','))
        
        # Haversine formula to calculate distance
        R = 6371  # Earth radius in km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance_km = R * c
        
        # Adjust speed based on vehicle type
        speed_kmh = 60  # Default speed
        if vehicle_type == "Motorcycle":
            speed_kmh = 50
        elif vehicle_type == "SUV":
            speed_kmh = 55
        elif vehicle_type == "Bus":
            speed_kmh = 45
        elif vehicle_type == "Truck":
            speed_kmh = 40
            
        # Calculate time in hours
        travel_time = distance_km / speed_kmh
        
        # Add buffer for traffic, stops, etc.
        travel_time *= 1.3
        
        return travel_time
        
    except:
        # Fallback: return a reasonable estimate
        return 1.5  # 1.5 hours between stops

def validate_coordinates(coords):
    """Validate coordinates format and realistic values"""
    if not coords or not isinstance(coords, str):
        return False
    
    # Check format: should be "lat,lng"
    if ',' not in coords:
        return False
    
    try:
        lat_str, lng_str = coords.split(',', 1)
        lat = float(lat_str.strip())
        lng = float(lng_str.strip())
        
        # Check if coordinates are within realistic bounds for Earth
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            return False
            
        # Additional check for obviously invalid coordinates
        if lat == 0.0 and lng == 0.0:  # Null Island
            return False
            
        return True
        
    except (ValueError, AttributeError):
        return False

def generate_realistic_coordinates(start_location, end_location, index, total_stops):
    """
    Generate realistic coordinates between start and end locations
    This is a fallback when AI generates invalid coordinates
    """
    # Simple interpolation between start and end
    # In a real application, you'd use geocoding here
    try:
        # Example coordinates for major Indian cities as fallbacks
        indian_cities = {
            "delhi": "28.6139,77.2090",
            "mumbai": "19.0760,72.8777",
            "chennai": "13.0827,80.2707",
            "bangalore": "12.9716,77.5946",
            "kolkata": "22.5726,88.3639",
            "hyderabad": "17.3850,78.4867",
            "pune": "18.5204,73.8567",
            "ahmedabad": "23.0225,72.5714",
            "jaipur": "26.9124,75.7873",
            "lucknow": "26.8467,80.9462"
        }
        
        # Try to find the city in our fallback list
        location_lower = start_location.lower() + " " + end_location.lower()
        for city, coords in indian_cities.items():
            if city in location_lower:
                return coords
                
        # Default to Delhi if no match found
        return "28.6139,77.2090"
        
    except:
        return "28.6139,77.2090"  # Default to Delhi coordinates