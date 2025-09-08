import google.generativeai as genai
import json
import streamlit as st
from utils import find_best_model

def generate_packing_list_prompt(trip_data, num_people, budget, additional_context=""):
    """
    Create a prompt for generating a packing list based on trip details
    """
    stops_info = "\n".join([
        f"- {stop['name']} ({stop['type']}): {stop.get('description', '')}"
        for stop in trip_data.get('stops', [])
    ])
    
    return f"""
    You are an expert travel packing advisor. Generate a comprehensive packing list for the following trip:
    
    TRIP DETAILS:
    - Route: {trip_data.get('start', 'Unknown')} to {trip_data.get('end', 'Unknown')}
    - Duration: {trip_data.get('total_trip_time', 'Unknown')}
    - Travelers: {num_people} people
    - Budget: {budget}
    - Vehicle: {trip_data.get('vehicle_suggestion', 'Car')}
    
    STOPS AND ACTIVITIES:
    {stops_info}
    
    ADDITIONAL CONTEXT:
    {additional_context}
    
    Generate a detailed packing list organized by categories. Consider:
    1. Clothing appropriate for activities and weather
    2. Essential documents and money
    3. Electronics and gadgets
    4. Health and hygiene items
    5. Vehicle-specific items if applicable
    6. Entertainment for the journey
    7. Budget-conscious items if applicable
    
    Return your response as JSON with this structure:
    {{
        "trip_summary": "brief_description",
        "packing_categories": [
            {{
                "category": "category_name",
                "items": [
                    {{
                        "item": "item_name",
                        "quantity": "recommended_quantity",
                        "importance": "essential|recommended|optional",
                        "notes": "any_notes"
                    }}
                ]
            }}
        ],
        "special_recommendations": "any_special_advice_based_on_the_trip"
    }}
    
    Only return the JSON object, no additional text.
    Make the suggestions practical and tailored to {num_people} people with a {budget} budget.
    """

def get_packing_list_recommendations(trip_data, api_key, num_people=2, budget="Moderate", additional_context=""):
    """
    Get packing list recommendations from Gemini model
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
        
        # Create packing list prompt
        prompt = generate_packing_list_prompt(trip_data, num_people, budget, additional_context)
        
        # Generate content
        response = model.generate_content(prompt)
        
        # Parse the response
        packing_data = parse_packing_response(response.text)
        return packing_data
        
    except Exception as e:
        return {"error": f"Error getting packing list: {str(e)}"}

def parse_packing_response(response_text):
    """
    Extract structured packing data from LLM response
    """
    try:
        # Try to find JSON in the response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            packing_data = json.loads(json_str)
            return packing_data
    except:
        pass
    
    # Fallback if no JSON found or parsing failed
    return get_fallback_packing_list()

def get_fallback_packing_list():
    """Get fallback packing list data"""
    return {
        "trip_summary": "General travel packing list",
        "packing_categories": [
            {
                "category": "Clothing",
                "items": [
                    {"item": "T-shirts", "quantity": "3-4 per person", "importance": "essential", "notes": "Comfortable for travel"},
                    {"item": "Pants/Jeans", "quantity": "2-3 pairs", "importance": "essential", "notes": "Versatile for various activities"},
                    {"item": "Jacket", "quantity": "1 per person", "importance": "essential", "notes": "For cooler evenings"},
                    {"item": "Comfortable shoes", "quantity": "1-2 pairs", "importance": "essential", "notes": "For walking and activities"}
                ]
            },
            {
                "category": "Documents & Money",
                "items": [
                    {"item": "ID/Passport", "quantity": "1 per person", "importance": "essential", "notes": "Required for identification"},
                    {"item": "Cash", "quantity": "As needed", "importance": "essential", "notes": "For small purchases and emergencies"},
                    {"item": "Credit/Debit cards", "quantity": "1-2", "importance": "essential", "notes": "Primary payment method"}
                ]
            },
            {
                "category": "Electronics",
                "items": [
                    {"item": "Phone charger", "quantity": "1 per person", "importance": "essential", "notes": "Keep devices powered"},
                    {"item": "Power bank", "quantity": "1-2", "importance": "recommended", "notes": "Backup power source"},
                    {"item": "Camera", "quantity": "1", "importance": "optional", "notes": "For photography enthusiasts"}
                ]
            }
        ],
        "special_recommendations": "Pack light and consider laundry options if traveling for extended periods."
    }

def display_packing_list(packing_data):
    """Display packing list in a user-friendly format"""
    if not packing_data or "error" in packing_data:
        return "<p>Could not generate packing list.</p>"
    
    html_output = f"""
    <div style="background: white; border-radius: 15px; padding: 20px; margin: 20px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
        <h3 style="color: #2d3748; margin-bottom: 20px;">🎒 Packing List</h3>
        <p style="color: #4a5568; margin-bottom: 25px;"><strong>Trip Summary:</strong> {packing_data.get('trip_summary', '')}</p>
    """
    
    for category in packing_data.get("packing_categories", []):
        html_output += f"""
        <div style="margin-bottom: 25px;">
            <h4 style="color: #667eea; margin-bottom: 15px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">{category['category']}</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">
        """
        
        for item in category.get("items", []):
            importance_color = {
                "essential": "#E53E3E",
                "recommended": "#D69E2E",
                "optional": "#38A169"
            }.get(item.get("importance", "optional"), "#4A5568")
            
            html_output += f"""
            <div style="background: #f7fafc; padding: 15px; border-radius: 10px; border-left: 4px solid {importance_color};">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                    <strong style="color: #2d3748;">{item['item']}</strong>
                    <span style="background: {importance_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: 600;">
                        {item.get('importance', 'optional').upper()}
                    </span>
                </div>
                <div style="color: #4a5568; font-size: 0.9rem;">
                    <div style="margin-bottom: 5px;"><strong>Quantity:</strong> {item.get('quantity', 'As needed')}</div>
                    <div>{item.get('notes', '')}</div>
                </div>
            </div>
            """
        
        html_output += "</div></div>"
    
    if packing_data.get("special_recommendations"):
        html_output += f"""
        <div style="background: #EBF8FF; padding: 15px; border-radius: 10px; margin-top: 20px; border-left: 4px solid #3182CE;">
            <h5 style="color: #2C5282; margin-bottom: 10px;">💡 Special Recommendations</h5>
            <p style="color: #2C5282; margin: 0;">{packing_data['special_recommendations']}</p>
        </div>
        """
    
    html_output += "</div>"
    return html_output