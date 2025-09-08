import requests
import json
import time
from datetime import datetime, timedelta
import streamlit as st
from utils import calculate_travel_time, validate_coordinates, generate_realistic_coordinates

class TrafficIntegration:
    def __init__(self, google_maps_api_key):
        self.api_key = google_maps_api_key
        self.base_url = "https://maps.googleapis.com/maps/api/directions/json"
    
    def get_traffic_aware_route(self, origin, destination, departure_time="now", vehicle_type="car"):
        """Get route with real-time traffic consideration"""
        # Validate coordinates format using the imported function
        if not validate_coordinates(origin) or not validate_coordinates(destination):
            return None
        
        params = {
            "origin": origin,
            "destination": destination,
            "departure_time": departure_time,
            "traffic_model": "best_guess",
            "key": self.api_key,
            "vehicleType": vehicle_type.lower()
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if data["status"] == "OK":
                route = data["routes"][0]
                leg = route["legs"][0]
                
                # Extract traffic information
                traffic_info = {
                    "distance": leg["distance"]["text"],
                    "duration": leg["duration"]["text"],
                    "duration_in_traffic": leg.get("duration_in_traffic", {}).get("text", "N/A"),
                    "departure_time": departure_time,
                    "summary": route["summary"],
                    "warnings": route.get("warnings", [])
                }
                
                # Get detailed steps with traffic data
                traffic_info["steps"] = []
                for step in leg["steps"]:
                    traffic_info["steps"].append({
                        "instruction": step["html_instructions"],
                        "distance": step["distance"]["text"],
                        "duration": step["duration"]["text"],
                        "travel_mode": step["travel_mode"]
                    })
                
                return traffic_info
            elif data["status"] == "ZERO_RESULTS":
                st.warning(f"Google Maps couldn't find a route between these points. Using estimated times.")
                return None
            else:
                st.warning(f"Google Maps API error: {data['status']}. Using estimated times.")
                return None
                
        except Exception as e:
            st.error(f"Error fetching traffic data: {str(e)}")
            return None
    
    def get_traffic_aware_time_estimate(self, start_coords, end_coords, vehicle_type="car"):
        """Get time estimate considering current traffic"""
        # Validate coordinates using the imported function
        if not validate_coordinates(start_coords) or not validate_coordinates(end_coords):
            return calculate_travel_time(start_coords, end_coords, vehicle_type)
        
        origin = f"{start_coords}"
        destination = f"{end_coords}"
        
        route_info = self.get_traffic_aware_route(origin, destination, vehicle_type=vehicle_type)
        
        if route_info and "duration_in_traffic" in route_info:
            # Extract hours from duration text (e.g., "2 hours 30 mins" -> 2.5)
            time_text = route_info["duration_in_traffic"]
            hours = 0
            if "hour" in time_text:
                hours = float(time_text.split("hour")[0].strip())
            if "min" in time_text:
                mins_text = time_text.split("min")[0].split()[-1]
                minutes = float(mins_text) / 60
                hours += minutes
            return hours
        else:
            # Fallback to our own calculation
            return calculate_travel_time(start_coords, end_coords, vehicle_type)
    
    def get_alternative_routes(self, origin, destination, departure_time="now"):
        """Get alternative routes to avoid traffic"""
        # Validate coordinates using the imported function
        if not validate_coordinates(origin) or not validate_coordinates(destination):
            return []
            
        params = {
            "origin": origin,
            "destination": destination,
            "departure_time": departure_time,
            "alternatives": "true",
            "key": self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if data["status"] == "OK":
                alternatives = []
                for route in data["routes"]:
                    leg = route["legs"][0]
                    alternatives.append({
                        "summary": route["summary"],
                        "distance": leg["distance"]["text"],
                        "duration": leg["duration"]["text"],
                        "duration_in_traffic": leg.get("duration_in_traffic", {}).get("text", "N/A"),
                        "warnings": route.get("warnings", [])
                    })
                return alternatives
            else:
                return []
                
        except Exception as e:
            st.error(f"Error fetching alternative routes: {str(e)}")
            return []
    
    def get_road_conditions(self, coordinates, radius=5000):
        """Get road conditions and incidents near coordinates"""
        # This would use a different API (like Here Maps or specialized traffic data)
        # For now, we'll return mock data
        return {
            "incidents": [
                {
                    "type": "accident",
                    "severity": "moderate",
                    "description": "Vehicle breakdown on shoulder",
                    "distance": "2.3 km ahead"
                }
            ],
            "construction": [
                {
                    "description": "Road work ahead",
                    "impact": "Lane closure",
                    "distance": "5.1 km ahead"
                }
            ]
        }

def optimize_itinerary_with_traffic(trip_data, google_maps_api_key):
    """Adjust itinerary based on current traffic conditions"""
    traffic_integration = TrafficIntegration(google_maps_api_key)
    optimized_data = trip_data.copy()
    
    if "stops" not in optimized_data or len(optimized_data["stops"]) < 2:
        return optimized_data
    
    # Update travel times between stops
    total_driving_time = 0
    stops = optimized_data["stops"]
    
    for i in range(len(stops) - 1):
        start_coords = stops[i]["coordinates"]
        end_coords = stops[i + 1]["coordinates"]
        
        # Validate coordinates before making API call using the imported function
        if not validate_coordinates(start_coords) or not validate_coordinates(end_coords):
            # Use fallback calculation
            travel_time = calculate_travel_time(start_coords, end_coords, optimized_data.get("vehicle_suggestion", "Car"))
        else:
            # Get traffic-aware time estimate
            travel_time = traffic_integration.get_traffic_aware_time_estimate(
                start_coords, end_coords, optimized_data.get("vehicle_suggestion", "Car")
            )
        
        total_driving_time += travel_time
        
        # Add traffic info to the stop (for display purposes)
        if i == 0:  # Only add to first stop to avoid duplication
            stops[i]["traffic_info"] = {
                "to_next_stop": f"{travel_time:.1f} hours",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "source": "Google Maps API" if validate_coordinates(start_coords) and validate_coordinates(end_coords) else "Estimated"
            }
    
    # Update total driving time
    optimized_data["total_driving_time"] = f"{total_driving_time:.1f} hours"
    
    # Calculate new total trip time
    total_visiting_time = sum(
        float(stop.get("visiting_time", 0.5)) if isinstance(stop.get("visiting_time"), (int, float)) else 0.5
        for stop in stops
    )
    optimized_data["total_trip_time"] = f"{total_driving_time + total_visiting_time:.1f} hours"
    
    # Only try to get alternative routes if we have valid coordinates
    first_stop = stops[0]
    last_stop = stops[-1]
    if (validate_coordinates(first_stop["coordinates"]) and 
        validate_coordinates(last_stop["coordinates"])):
        
        origin = f"{first_stop['coordinates']}"
        destination = f"{last_stop['coordinates']}"
        alternatives = traffic_integration.get_alternative_routes(origin, destination)
        
        if alternatives:
            optimized_data["alternative_routes"] = alternatives
            optimized_data["traffic_alert"] = "Heavy traffic detected. Consider alternative routes."
    
    return optimized_data