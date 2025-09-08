import urllib.parse
import streamlit as st

def generate_google_maps_directions_link(trip_data):
    """
    Generate a Google Maps directions link for the entire trip.
    """
    stops = trip_data.get("stops", [])
    if not stops:
        return ""
    
    valid_stops = [stop for stop in stops if stop.get("coordinates")]
    if not valid_stops:
        return ""
    
    # Start point
    start_coords = valid_stops[0].get('coordinates', "")
    
    # End point
    end_coords = valid_stops[-1].get('coordinates', "")
    
    # Waypoints (all stops between start and end)
    waypoints = [stop.get("coordinates", "") for stop in valid_stops[1:-1] if stop.get("coordinates")]
    
    # Construct the Google Maps URL
    base_url = "https://www.google.com/maps/dir/"
    
    # URL encode all components
    start_encoded = urllib.parse.quote(start_coords)
    end_encoded = urllib.parse.quote(end_coords)
    waypoints_encoded = "/".join([urllib.parse.quote(wp) for wp in waypoints])
    
    if waypoints:
        directions_url = f"{base_url}{start_encoded}/{waypoints_encoded}/{end_encoded}"
    else:
        directions_url = f"{base_url}{start_encoded}/{end_encoded}"
    
    return directions_url

def create_static_map_url(trip_data, maps_api_key):
    """
    Generate a URL for a static Google Map image with a thick black path and colored markers.
    """
    stops = trip_data.get("stops", [])
    if not stops:
        return ""

    base_url = "https://maps.googleapis.com/maps/api/staticmap?"
    
    # Path with thick black line
    path_coords = "|".join([stop.get("coordinates", "") for stop in stops if stop.get("coordinates")])
    path = f"path=color:0x000000FF|weight:8|{path_coords}"
    
    # Markers
    markers = []
    if stops and stops[0].get('coordinates'):
        start_coords = stops[0]['coordinates']
        markers.append(f"markers=color:green|label:S|{start_coords}")
    
    if len(stops) > 1 and stops[-1].get('coordinates'):
        end_coords = stops[-1]['coordinates']
        markers.append(f"markers=color:red|label:E|{end_coords}")
        
    for i, stop in enumerate(stops[1:-1]):
        if stop.get('coordinates'):
            stop_coords = stop['coordinates']
            label = chr(65 + i)
            markers.append(f"markers=color:orange|label:{label}|{stop_coords}")
            
    map_url = (
        f"{base_url}"
        f"{path}"
        f"&{'&'.join(markers)}"
        f"&size=800x400"
        f"&key={maps_api_key}"
    )
    return map_url

def create_dynamic_map_html(trip_data, maps_api_key):
    """
    Generate HTML for an interactive Google Map with an optimized route.
    """
    stops = trip_data.get("stops", [])
    if not stops:
        return "<p>No stops data available to generate map.</p>"

    valid_stops = [stop for stop in stops if stop.get("coordinates")]
    if not valid_stops:
        return "<p>No valid coordinates found for any stops.</p>"

    start_coords = valid_stops[0].get('coordinates', "")
    
    # Create the waypoints string for the URL, with optimization enabled
    waypoints = "optimize:true|" + "|".join([stop.get("coordinates", "") for stop in valid_stops[1:-1] if stop.get("coordinates")])
    
    # URL encode the start, end, and waypoints
    start_encoded = urllib.parse.quote(start_coords)
    end_encoded = urllib.parse.quote(valid_stops[-1].get('coordinates', ""))
    waypoints_encoded = urllib.parse.quote(waypoints)
    
    # Construct the Google Maps Embed URL
    map_url = (
        f"https://www.google.com/maps/embed/v1/directions"
        f"?key={maps_api_key}"
        f"&origin={start_encoded}"
        f"&destination={end_encoded}"
        f"&waypoints={waypoints_encoded}"
    )

    return f"""
    <iframe
        width="100%"
        height="500"
        frameborder="0"
        style="border:0; border-radius: 12px;"
        src="{map_url}"
        allowfullscreen>
    </iframe>
    """

def create_stop_map_html(coordinates, place_name, maps_api_key):
    """
    Generate HTML for a simple embedded map for a single stop.
    """
    if not coordinates:
        return "<p>Map not available for this stop.</p>"
    
    try:
        encoded_place = urllib.parse.quote(f"{place_name}@{coordinates}")
        
        map_url = f"https://www.google.com/maps/embed/v1/place?key={maps_api_key}&q={encoded_place}"
        
        return f"""
        <iframe
            width="100%"
            height="200"
            frameborder="0"
            style="border:0; border-radius: 12px;"
            src="{map_url}"
            allowfullscreen>
        </iframe>
        """
    except Exception as e:
        return f"<p>Error generating map: {e}</p>"