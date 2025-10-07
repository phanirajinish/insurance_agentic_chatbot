import logging
import json
from datetime import datetime

def setup_logging():
    """Setup logging configuration for the chatbot."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/conversations.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def format_conversation_log(user_input, bot_response, user_profile, intent, tokens_used):
    """Format conversation data for logging."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_input": user_input,
        "bot_response": bot_response,
        "intent": intent,
        "tokens_used": tokens_used,
        "user_profile": {
            "gender": user_profile.get("gender"),
            "location": user_profile.get("location"),
            "member_count": len(user_profile.get("members", []))
        }
    }
    return json.dumps(log_entry)

def format_table_data(data, headers):
    """Format data for table display in Streamlit."""
    if not data:
        return []
    
    formatted_data = []
    for item in data:
        row = []
        for header in headers:
            row.append(item.get(header, "N/A"))
        formatted_data.append(row)
    
    return formatted_data

def validate_profile_completeness(profile):
    """Validate if user profile has all required fields."""
    required_fields = ["gender", "location", "members"]
    missing = []
    
    for field in required_fields:
        if not profile.get(field):
            missing.append(field)
    
    # Check if self member with valid age exists
    if profile.get("members"):
        has_self = any(
            m.get("relation") == "self" and isinstance(m.get("age"), int) and m["age"] >= 18
            for m in profile["members"]
        )
        if not has_self:
            missing.append("self_age")
    
    return len(missing) == 0, missing
