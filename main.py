import streamlit as st
import google.generativeai as genai
import os
import json
import re
import urllib.parse
from dotenv import load_dotenv
from utils import get_available_models, find_best_model, calculate_travel_time
from prompts import create_travel_prompt
from map_generator import create_static_map_url, create_dynamic_map_html, create_stop_map_html, generate_google_maps_directions_link
from traffic_integration import optimize_itinerary_with_traffic
from packing_list import get_packing_list_recommendations, display_packing_list

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="AI Travel Planner Pro",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize API keys
if "GEMINI_API_KEY" not in st.session_state:
    st.session_state.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if "GOOGLE_MAPS_API_KEY" not in st.session_state:
    st.session_state.GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Custom CSS for modern styling with updated colors
st.markdown("""
<style>
    /* Main styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .stApp {
        background: #f8f9fa;
    }
    
    /* Header styling */
    .main-header {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        padding: 1rem;
        color: black
    }
    
    .sub-header {
        font-size: 1.8rem;
        color: #2d3748;
        font-weight: 600;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    /* Card styling */
    .card {
        background: white;
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border: none;
        transition: transform 0.3s ease;
        color: black
    }

    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.15);
    }
    
    /* Describe Your Journey card */
    .journey-card {
        background: linear-gradient(135deg, #7E57C2 0%, #5E35B1 100%);
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(126, 87, 194, 0.3);
        border: none;
        color: white;
        transition: transform 0.3s ease;
    }
    
    .journey-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(126, 87, 194, 0.4);
    }
    
    /* Trip Inspiration card */
    .inspiration-card {
        background: linear-gradient(135deg, #9575CD 0%, #673AB7 100%);
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(149, 117, 205, 0.3);
        border: none;
        color: white;
        transition: transform 0.3s ease;
    }
    
    .inspiration-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(149, 117, 205, 0.4);
    }
    
    /* Travel Tips card */
    .tips-card {
        background: linear-gradient(135deg, #7986CB 0%, #3949AB 100%);
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(121, 134, 203, 0.3);
        border: none;
        color: white;
        transition: transform 0.3s ease;
    }
    
    .tips-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(121, 134, 203, 0.4);
    }
    
    /* Journey Starter card */
    .journey-starter {
        background: linear-gradient(135deg, #64B5F6 0%, #1976D2 100%);
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        margin-top: 30px;
        color: white;
        box-shadow: 0 10px 30px rgba(25, 118, 210, 0.3);
    }
    
    .journey-starter h3 {
        color: white;
        font-size: 2rem;
        margin-bottom: 15px;
    }
    
    .journey-starter p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.2rem;
        margin-bottom: 20px;
    }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Input styling */
    .stTextArea textarea {
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        padding: 15px;
        font-size: 1rem;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 15px;
        text-align: center;
        color: white;
        margin: 10px;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 5px;
    }
    
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
        font-weight: 500;
    }
    
    /* Stop cards */
    .stop-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        border-left: 5px solid #667eea;
        color: black
    }
    
    .stop-number {
        background: #667eea;
        color: white;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 1.2rem;
        margin-right: 15px;
    }
    
    /* Prompt suggestions */
    .prompt-suggestion {
        background: white;
        border-radius: 16px;
        padding: 20px;
        margin: 12px 0;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 2px solid #e2e8f0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    
    .prompt-suggestion:hover {
        border-color: #667eea;
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
    }
    
    .prompt-icon {
        font-size: 1.5rem;
        margin-right: 12px;
        color: #667eea;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
    }
    
    .sidebar-header {
        color: white;
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 2rem;
    }
    
    /* Map container */
    .map-container {
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        margin: 20px 0;
        height: 500px;
    }
    
    .static-map {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    .dynamic-map {
        width: 100%;
        height: 100%;
        border: none;
    }
    
    .stop-map {
        width: 100%;
        height: 200px;
        border-radius: 12px;
        margin-top: 15px;
        border: none;
    }
    
    /* Success message */
    .success-msg {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        padding: 20px;
        border-radius: 16px;
        text-align: center;
        font-weight: 600;
        margin: 20px 0;
    }
    
    /* Map tabs */
    .map-tabs {
        display: flex;
        gap: 10px;
        margin-bottom: 15px;
    }
    
    .map-tab {
        padding: 10px 20px;
        border-radius: 8px;
        background: #e2e8f0;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .map-tab.active {
        background: #667eea;
        color: white;
    }
    
    .map-tab:hover {
        background: #cbd5e0;
    }
    
    .map-tab.active:hover {
        background: #5a67d8;
    }
</style>
""", unsafe_allow_html=True)

# Function to get trip recommendations from Gemini model
def get_trip_recommendations(prompt, api_key, vehicle_type=None, num_people=2, budget="Moderate"):
    """
    Get trip recommendations from Gemini model
    """
    try:
        if not api_key:
            return {"error": "API key not provided"}
            
        genai.configure(api_key=api_key)
        
        # Find the best available model
        model_name = find_best_model(api_key)
        if not model_name:
            return {"error": "No suitable model found"}
        
        # Create the model
        model = genai.GenerativeModel(model_name)
        
        # Create enhanced prompt
        enhanced_prompt = create_travel_prompt(prompt, vehicle_type, num_people, budget)
        
        # Generate content
        response = model.generate_content(enhanced_prompt)
        
        # Parse the response
        trip_data = parse_trip_response(response.text)
        return trip_data
        
    except Exception as e:
        return {"error": f"Error getting LLM response: {str(e)}"}
    
def validate_and_fix_trip_data(trip_data):
    """Validate and fix coordinates in trip data"""
    if "stops" not in trip_data:
        return trip_data
    
    from utils import validate_coordinates, generate_realistic_coordinates
    
    stops = trip_data["stops"]
    
    # Fix coordinates for each stop
    for i, stop in enumerate(stops):
        if not validate_coordinates(stop.get("coordinates", "")):
            # Generate realistic coordinates as fallback
            stop["coordinates"] = generate_realistic_coordinates(
                trip_data.get("start", "Delhi"),
                trip_data.get("end", "Mumbai"),
                i,
                len(stops)
            )
            stop["coordinates_fixed"] = True  # Mark as fixed
    
    return trip_data
    
def get_traffic_aware_recommendations(prompt, api_key, maps_api_key, vehicle_type=None, num_people=2, budget="Moderate"):
    """
    Get trip recommendations with real-time traffic consideration
    """
    # First get the standard recommendations
    trip_data = get_trip_recommendations(
        prompt, api_key, vehicle_type, num_people, budget
    )
    if "error" in trip_data:
        return trip_data
    
    # Validate and fix coordinates before traffic processing
    trip_data = validate_and_fix_trip_data(trip_data)
    
    # Then optimize with traffic data
    if maps_api_key and maps_api_key.strip():
        try:
            return optimize_itinerary_with_traffic(trip_data, maps_api_key)
        except Exception as e:
            st.warning("Could not fetch real-time traffic data. Using estimated times.")
            return trip_data
    else:
        return trip_data

def parse_trip_response(response_text):
    """
    Extract structured trip data from LLM response
    """
    try:
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            trip_data = json.loads(json_str)
            return trip_data
    except:
        pass
    
    # Fallback if no JSON found or parsing failed
    return get_fallback_trip_data()

def generate_packing_list(trip_data, api_key, num_people, budget):
    """Generate packing list based on trip data"""
    with st.spinner("🧳 Generating smart packing list..."):
        packing_data = get_packing_list_recommendations(
            trip_data, api_key, num_people, budget
        )
        return packing_data

def get_fallback_trip_data():
    """Get fallback trip data"""
    return {
        "start": "New Delhi",
        "end": "Agra",
        "total_driving_distance": "240 km",
        "total_driving_time": "4 hours",
        "total_visiting_time": "5 hours",
        "total_trip_time": "9 hours",
        "vehicle_suggestion": "Sedan or SUV",
        "stops": [
            {
                "name": "Mathura - Krishna Janmabhoomi", 
                "type": "temple", 
                "coordinates": "27.4924,77.6737",
                "description": "Sacred birthplace of Lord Krishna",
                "visiting_time": 1.5,
                "rating": "4.7"
            },
            {
                "name": "Vrindavan - Banke Bihari Temple", 
                "type": "temple", 
                "coordinates": "27.5810,77.6960",
                "description": "Famous temple dedicated to Lord Krishna",
                "visiting_time": 1.0,
                "rating": "4.8"
            },
            {
                "name": "Fatehpur Sikri", 
                "type": "historical", 
                "coordinates": "27.0945,77.6679",
                "description": "Mughal era historical site and UNESCO World Heritage Site",
                "visiting_time": 2.0,
                "rating": "4.6"
            }
        ],
        "additional_recommendations": "Start early to avoid traffic. The Taj Mahal is best visited at sunrise or sunset for the best experience."
    }
def generate_packing_list(trip_data, api_key, num_people, budget):
    """Generate packing list based on trip data"""
    with st.spinner("🧳 Generating smart packing list..."):
        packing_data = get_packing_list_recommendations(
            trip_data, api_key, num_people, budget
        )
        return packing_data

def format_packing_list_for_download(packing_data):
    """Format packing list for text download"""
    if not packing_data or 'error' in packing_data:
        return "Packing list not available. Please generate it first."
    text = "PACKING LIST\n"
    text += "=" * 50 + "\n\n"
    text += f"Trip: {packing_data.get('trip_summary', '')}\n\n"
    for category in packing_data.get("packing_categories", []):
        text += f"{category['category'].upper()}\n"
        text += "-" * len(category['category']) + "\n"
        for item in category.get("items", []):
            text += f"✓ {item['item']} ({item.get('quantity', 'As needed')})"
            text += f" - {item.get('importance', '').upper()}\n"
            if item.get('notes'):
                text += f"  Note: {item['notes']}\n"
            text += "\n"
        text += "\n"
    if packing_data.get("special_recommendations"):
        text += "SPECIAL RECOMMENDATIONS\n"
        text += "-" * 25 + "\n"
        text += f"{packing_data['special_recommendations']}\n"
    return text

# Initialize session state
if "current_prompt" not in st.session_state:
    st.session_state.current_prompt = ""
if "selected_map_type" not in st.session_state:
    st.session_state.selected_map_type = "dynamic"
if "traffic_last_updated" not in st.session_state:
    st.session_state.traffic_last_updated = None
if "packing_data" not in st.session_state:
    st.session_state.packing_data = None

# Sidebar for API configuration
with st.sidebar:
    st.markdown('<div class="sidebar-header">🔑 API Configuration</div>', unsafe_allow_html=True)
    
    gemini_key = st.text_input(
        "Gemini API Key", 
        value=st.session_state.GEMINI_API_KEY or "",
        type="password",
        help="Get from https://makersuite.google.com/",
        placeholder="Enter your Gemini API key here..."
    )
    
    maps_key = st.text_input(
        "Google Maps API Key", 
        value=st.session_state.GOOGLE_MAPS_API_KEY or "",
        type="password",
        help="Get from https://console.cloud.google.com/",
        placeholder="Enter your Google Maps API key here..."
    )
    
    if st.button("💾 Save API Keys", use_container_width=True):
        st.session_state.GEMINI_API_KEY = gemini_key
        st.session_state.GOOGLE_MAPS_API_KEY = maps_key
        st.success("API keys saved successfully!")
    
    st.markdown("---")
    
    st.markdown("""
    <div style='color: white; padding: 10px;'>
    <h4>🚀 Features</h4>
    <ul style='margin-left: 15px;'>
        <li>AI-Powered Route Planning</li>
        <li>Real-Time Traffic Updates</li>
        <li>Interactive Maps</li>
        <li>Smart Stop Recommendations</li>
        <li>Real-time Guidance</li>
        <li>Vehicle Suggestions</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# Main app
st.markdown('<h1 class="main-header">✈️ AI Travel Planner Pro</h1>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Plan Your Perfect Journey with AI Intelligence</div>', unsafe_allow_html=True)

# Main content in two columns
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("""
    <div class="journey-card">
        <h3>🎯 Describe Your Journey</h3>
        <p>Tell us about your dream trip and we'll create the perfect itinerary!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Prompt input
    prompt = st.text_area(
        "**Your Trip Details:**",
        value=st.session_state.current_prompt,
        height=150,
        placeholder="Example: I want to travel from Delhi to Agra with stops at historical sites and good local restaurants...",
        label_visibility="collapsed"
    )
    
    # Options for customization
    with st.expander("⚙️ Advanced Settings", expanded=True):
        col_a, col_b = st.columns(2)
        with col_a:
            num_people = st.number_input("👥 Number of Travelers", 1, 10, 2)
        with col_b:
            budget = st.selectbox(
                "💰 Budget Level",
                ["Budget", "Moderate", "Luxury"],
                index=1
            )
    
    # Generate trip plan button
    if st.button("🚀 Generate Travel Plan", type="primary", use_container_width=True):
        st.session_state.generate_clicked = True
        st.session_state.current_prompt = prompt

with col2:
    st.markdown("""
    <div class="inspiration-card">
        <h3>💡 Trip Inspiration</h3>
        <p>Need ideas? Try one of these popular routes:</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Prompt suggestions
    prompt_suggestions = [
        {"icon": "🕉️", "text": "Spiritual journey from Varanasi to Rishikesh with temple visits"},
        {"icon": "🏖️", "text": "Beach hopping itinerary from Mumbai to Goa"},
        {"icon": "⛰️", "text": "Himalayan road trip from Delhi to Leh with scenic stops"},
        {"icon": "🍛", "text": "Food tour from Hyderabad to Chennai with local cuisine"},
        {"icon": "🐘", "text": "Wildlife safari from Bangalore to Bandipur and Nagarhole"},
        {"icon": "🏰", "text": "Heritage tour from Jaipur to Udaipur with palace visits"}
    ]
    
    for i, suggestion in enumerate(prompt_suggestions):
        if st.button(f"{suggestion['icon']} {suggestion['text']}", key=f"prompt_{i}", use_container_width=True):
            st.session_state.suggestion_clicked = suggestion['text']

# Handle prompt suggestions
if 'suggestion_clicked' in st.session_state:
    st.session_state.current_prompt = st.session_state.suggestion_clicked
    st.session_state.generate_clicked = True
    del st.session_state.suggestion_clicked

# Generate trip plan if button was clicked
if 'generate_clicked' in st.session_state and st.session_state.generate_clicked:
    prompt = st.session_state.current_prompt
    
    if not prompt:
        st.error("Please describe your trip first!")
    elif not st.session_state.GEMINI_API_KEY:
        st.error("Please enter your Gemini API key in the sidebar")
    elif not st.session_state.GOOGLE_MAPS_API_KEY:
        st.error("Please enter your Google Maps API key in the sidebar")
    else:
        with st.spinner("🧠 AI is crafting your perfect itinerary..."):
            # Get trip recommendations from LLM
            trip_data = get_traffic_aware_recommendations(
                prompt, 
                st.session_state.GEMINI_API_KEY,
                st.session_state.GOOGLE_MAPS_API_KEY,
                vehicle_type=None,  # Add this parameter
                num_people=num_people,
                budget=budget
            )
            
            if trip_data and "error" not in trip_data:
                st.session_state.trip_data = trip_data
                st.session_state.plan_generated = True
                st.session_state.traffic_last_updated = "Just now"

# Display generated trip plan
if 'plan_generated' in st.session_state and st.session_state.plan_generated:
    trip_data = st.session_state.trip_data
    st.markdown('<div class="success-msg">✅ Your Travel Plan is Ready!</div>', unsafe_allow_html=True)
    
    # Traffic refresh button
    if st.button("🔄 Refresh Traffic Conditions", key="refresh_traffic"):
        with st.spinner("Updating traffic conditions..."):
            st.session_state.trip_data = optimize_itinerary_with_traffic(
                st.session_state.trip_data, 
                st.session_state.GOOGLE_MAPS_API_KEY
            )
            st.session_state.traffic_last_updated = "Just now"
        st.rerun()
    
    if st.session_state.traffic_last_updated:
        st.caption(f"Traffic data last updated: {st.session_state.traffic_last_updated}")

    # Route overview
    st.markdown(f'<h2 style="text-align: center; color: #2d3748;">🗺️ {trip_data["start"]} to {trip_data["end"]}</h2>', unsafe_allow_html=True)
    
    # Metrics in cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(trip_data["stops"])}</div>
            <div class="metric-label">TOTAL STOPS</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{trip_data.get("total_driving_time", "N/A")}</div>
            <div class="metric-label">DRIVING TIME</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{trip_data.get("total_visiting_time", "N/A")}</div>
            <div class="metric-label">VISITING TIME</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{trip_data.get("vehicle_suggestion", "Car")}</div>
            <div class="metric-label">VEHICLE</div>
        </div>
        """, unsafe_allow_html=True)

    # Traffic alerts
    if trip_data.get("traffic_alert"):
        st.markdown(f"""
        <div class="traffic-alert">
            <h4>🚧 Traffic Alert</h4>
            <p>{trip_data["traffic_alert"]}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Alternative routes
    if trip_data.get("alternative_routes"):
        st.markdown("### 🚗 Alternative Routes")
        st.info("Consider these alternative routes to avoid heavy traffic:")
        
        for i, route in enumerate(trip_data["alternative_routes"]):
            with st.expander(f"Alternative Route #{i+1}: {route['summary']}"):
                st.write(f"**Distance:** {route['distance']}")
                st.write(f"**Time without traffic:** {route['duration']}")
                st.write(f"**Time with traffic:** {route['duration_in_traffic']}")
                if route.get('warnings'):
                    st.warning("**Warnings:** " + ", ".join(route['warnings']))
    
    # Map selection tabs
    st.markdown("### 📍 Journey Maps")
    
    # Create tabs for different map types
    map_col1, map_col2 = st.columns([1, 5])
    with map_col1:
        st.markdown("**Map Type:**")
        map_type = st.radio("", ["Interactive", "Static"], label_visibility="collapsed", horizontal=True)
    
    # Display selected map
    if map_type == "Interactive":
        st.markdown("##### 🗺️ Interactive Map")
        map_html = create_dynamic_map_html(trip_data, st.session_state.GOOGLE_MAPS_API_KEY)
        st.components.v1.html(map_html, height=500, scrolling=False)
    else:
        st.markdown("##### 🗺️ Static Map")
        map_url = create_static_map_url(trip_data, st.session_state.GOOGLE_MAPS_API_KEY)
        st.image(map_url, use_column_width=True, output_format="PNG")
    
    # Google Maps link
    maps_link = generate_google_maps_directions_link(trip_data)
    st.markdown(f"""
    <div style="text-align: center; margin: 20px 0;">
        <a href="{maps_link}" target="_blank" style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 12px;
            font-weight: 600;
            display: inline-block;
        ">🗺️ Open in Google Maps</a>
    </div>
    """, unsafe_allow_html=True)
    
    # Recommended stops - ONLY SHOW IF trip_data EXISTS
    st.markdown("### 🛑 Recommended Stops")
    for i, stop in enumerate(trip_data["stops"]):
        visiting_time = stop.get("visiting_time", 0.5)
        
        # Generate the map HTML
        map_html = "<p>No map available</p>"
        if stop.get("coordinates"):
            map_html = create_stop_map_html(
                stop.get("coordinates", ""),
                stop["name"],
                st.session_state.GOOGLE_MAPS_API_KEY
            )

        # Create the complete stop card with map embedded
        traffic_info_html = ""
        if stop.get('traffic_info'):
            traffic_info_html = f"""
            <p><strong>🚦 Traffic to next stop:</strong> {stop['traffic_info']['to_next_stop']}
            <br><small>Updated: {stop['traffic_info']['last_updated']}</small></p>
            """

        st.markdown(f"""
        <div class="stop-card">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div class="stop-number">{i+1}</div>
                <h3 style="margin: 0; color: #2d3748;">{stop["name"]}</h3>
            </div>
            <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; align-items: start;">
                <div>
                    <p><strong>Type:</strong> {stop.get('type', 'N/A').title()}</p>
                    <p><strong>Time Needed:</strong> {visiting_time} hours</p>
                    <p><strong>Rating:</strong> ⭐ {stop.get('rating', 'N/A')}/5</p>
                    <p>{stop.get('description', 'No description available')}</p>
                </div>
                <div style="height: 200px; overflow: hidden; border-radius: 12px;">
                    {map_html}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Packing List Section - ADDED PACKING LIST HERE
    # Packing List Section - ADDED PACKING LIST HERE
    st.markdown("### 🎒 Smart Packing List")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("Generate Packing List", key="generate_packing", use_container_width=True):
            st.session_state.packing_data = generate_packing_list(
                trip_data, 
                st.session_state.GEMINI_API_KEY,
                num_people,
                budget
            )
            st.rerun()
    
    if 'packing_data' in st.session_state and st.session_state.packing_data is not None:
        if 'error' in st.session_state.packing_data:
            st.error("Error generating packing list. Please try again.")
        else:
            packing_html = display_packing_list(st.session_state.packing_data)
            # Use components.html to properly render HTML
            st.components.v1.html(packing_html, height=600, scrolling=True)
        
        # Add download button - ONLY SHOW IF PACKING DATA EXISTS
        with col2:
            if st.session_state.packing_data and 'error' not in st.session_state.packing_data:
                packing_text = format_packing_list_for_download(st.session_state.packing_data)
                st.download_button(
                    label="📥 Download Packing List",
                    data=packing_text,
                    file_name="packing_list.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            else:
                st.warning("Generate packing list first")

    # Additional recommendations
    if "additional_recommendations" in trip_data:
        st.markdown("""
        <div class="tips-card">
            <h3>💡 Travel Tips & Recommendations</h3>
            <p>{}</p>
        </div>
        """.format(trip_data["additional_recommendations"]), unsafe_allow_html=True)
        
else:
    # Show inspiration if no plan generated yet
    st.markdown("""
    <div class="journey-starter">
        <h3>🌟 Your Journey Starts Here</h3>
        <p>Describe your dream trip or choose from our suggestions to begin planning!</p>
        <div style="font-size: 4rem; margin: 20px 0;">✈️</div>
    </div>
    """, unsafe_allow_html=True)