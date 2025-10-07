"""
Premium API Integration for Apollo 24|7 Insurance
Fetches real-time premium quotes based on user profile
"""

import requests
import json
from typing import Dict, List, Optional

# API Configuration
PREMIUM_API_URL = "https://apigateway.apollo247.in/insurance-v2/api/v2/getAllProducts"
DEFAULT_HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json',
    'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
    'Referer': 'https://apollo247insurance.com/'
}

def convert_profile_to_api_format(user_profile: Dict) -> Dict:
    """
    Convert internal user profile to API request format.
    
    Args:
        user_profile: Internal profile format with members, gender, location
        
    Returns:
        API request payload
    """
    member_details_list = []
    
    # Extract members from profile
    members = user_profile.get("members", [])
    
    for member in members:
        relation = member.get("relation", "self")
        age = member.get("age", 30)
        
        # Get gender - check member-specific or profile-level
        gender = member.get("gender")
        if not gender and relation == "self":
            gender = user_profile.get("gender", "male")
        elif not gender:
            # Default gender based on relation
            if relation in ["father", "son"]:
                gender = "male"
            elif relation in ["mother", "daughter", "wife"]:
                gender = "female"
            else:
                gender = "male"  # default
        
        # Capitalize first letter for API
        gender = gender.capitalize()
        relation_formatted = relation.capitalize()
        
        member_details_list.append({
            "relation": relation_formatted,
            "age": age,
            "gender": gender
        })
    
    # If no members, create default self member
    if not member_details_list:
        member_details_list.append({
            "relation": "Self",
            "age": 30,
            "gender": user_profile.get("gender", "male").capitalize()
        })
    
    # Map location to pincode (approximation)
    location = user_profile.get("location", "Tier 1")
    pincode_map = {
        "tier 1": "560103",  # Bangalore
        "tier 2": "380001",  # Ahmedabad
        "tier 3": "462001"   # Bhopal
    }
    pincode = pincode_map.get(location.lower(), "560103")
    
    # Build API payload
    payload = {
        "filters": [],
        "selSortBy": "recommended",
        "memberDetailsList": member_details_list,
        "pincode": pincode,
        "quoteIdSumInsuredList": []
    }
    
    return payload


def fetch_premium_quotes(user_profile: Dict, auth_token: Optional[str] = None, timeout: int = 10) -> Dict:
    """
    Fetch premium quotes from Apollo API.
    
    Args:
        user_profile: User profile with members, gender, location
        auth_token: Optional authorization token (if None, will try without auth)
        timeout: Request timeout in seconds
        
    Returns:
        Dict with status, data, and error information
    """
    try:
        # Convert profile to API format
        payload = convert_profile_to_api_format(user_profile)
        
        # Prepare headers
        headers = DEFAULT_HEADERS.copy()
        if auth_token:
            headers['Authorization'] = auth_token
        
        # Make API request
        response = requests.post(
            PREMIUM_API_URL,
            headers=headers,
            json=payload,
            timeout=timeout
        )
        
        # Check response status
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "data": data,
                "error": None
            }
        elif response.status_code == 401:
            return {
                "status": "error",
                "data": None,
                "error": "Authentication failed. Please try again later."
            }
        else:
            return {
                "status": "error",
                "data": None,
                "error": f"API returned status code {response.status_code}"
            }
            
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "data": None,
            "error": "Request timed out. Please try again."
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "data": None,
            "error": f"Network error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "data": None,
            "error": f"Unexpected error: {str(e)}"
        }


def format_premium_response(api_response: Dict, top_n: int = 5) -> str:
    """
    Format API response into conversational text.
    
    Args:
        api_response: Response from fetch_premium_quotes
        top_n: Number of top plans to show
        
    Returns:
        Formatted string for chatbot response
    """
    if api_response["status"] == "error":
        return f"⚠️ I encountered an issue fetching live premium quotes: {api_response['error']}\n\nBut don't worry! I can still help you compare plans based on our knowledge base. Would you like to see plan recommendations?"
    
    data = api_response["data"]
    
    # Extract products
    products = data.get("products", [])
    
    if not products:
        return "I couldn't find any premium quotes at the moment. Would you like me to recommend plans based on your profile instead?"
    
    # Build response
    response = "💰 **Live Premium Quotes for Your Profile:**\n\n"
    
    # Show top N products
    for idx, product in enumerate(products[:top_n], 1):
        plan_name = product.get("productName", "Unknown Plan")
        insurer = product.get("insurerName", "")
        sum_insured = product.get("sumInsured", 0)
        premium = product.get("premium", 0)
        
        # Format sum insured
        si_formatted = f"₹{sum_insured:,}" if sum_insured < 100000 else f"₹{sum_insured/100000:.1f}L"
        
        # Format premium
        premium_formatted = f"₹{premium:,}"
        
        response += f"**{idx}. {plan_name}**"
        if insurer:
            response += f" by {insurer}"
        response += f"\n"
        response += f"   • Sum Insured: {si_formatted}\n"
        response += f"   • Annual Premium: **{premium_formatted}**\n"
        
        # Add key features if available
        features = product.get("keyFeatures", [])
        if features:
            response += f"   • Key Features: {', '.join(features[:3])}\n"
        
        response += "\n"
    
    if len(products) > top_n:
        response += f"_...and {len(products) - top_n} more plans available_\n\n"
    
    # Add follow-up
    response += "💡 **What would you like to do next?**\n"
    response += "• Want details about any specific plan?\n"
    response += "• Should I compare these plans?\n"
    response += "• Ready to connect with an advisor to purchase?\n"
    
    return response


def get_premium_quotes_conversational(user_profile: Dict, auth_token: Optional[str] = None) -> str:
    """
    One-stop function to fetch and format premium quotes.
    
    Args:
        user_profile: User profile dictionary
        auth_token: Optional auth token
        
    Returns:
        Formatted conversational response
    """
    # Fetch quotes
    api_response = fetch_premium_quotes(user_profile, auth_token)
    
    # Format response
    formatted = format_premium_response(api_response)
    
    return formatted


# Helper function to extract specific plan details
def get_plan_details(api_response: Dict, plan_name: str) -> Optional[Dict]:
    """
    Extract details for a specific plan from API response.
    
    Args:
        api_response: Response from fetch_premium_quotes
        plan_name: Name of the plan to find
        
    Returns:
        Plan details or None if not found
    """
    if api_response["status"] != "success":
        return None
    
    products = api_response["data"].get("products", [])
    
    for product in products:
        if plan_name.lower() in product.get("productName", "").lower():
            return product
    
    return None

