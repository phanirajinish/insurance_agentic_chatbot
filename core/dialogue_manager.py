from core.profile_extractor import gpt_profile_extractor

REQUIRED_FIELDS = ["gender", "location", "members"]

def is_profile_complete(profile):
    has_valid_self = any(
        m.get("relation") == "self" and isinstance(m.get("age"), int) and m["age"] >= 18
        for m in profile.get("members", [])
    )
    has_gender = profile.get("gender") is not None
    has_location = profile.get("location") is not None

    return has_valid_self and has_gender and has_location

def merge_members(existing, new):
    relation_map = {m['relation']: m for m in existing}
    for m in new:
        relation = m['relation']
        if relation in relation_map:
            # Only update fields that are present
            if 'age' in m and m['age'] is not None:
                relation_map[relation]['age'] = m['age']
        else:
            relation_map[relation] = m
    return list(relation_map.values())



def handle_dialogue(user_input, user_profile, intent, last_bot_action):
    # Step 1: Extract profile info from GPT
    new_info = gpt_profile_extractor(user_input)

    # Step 2: Merge profile
    updated_profile = dict(user_profile)
    updated_profile["gender"] = new_info.get("gender") or user_profile.get("gender")
    updated_profile["location"] = new_info.get("location") or user_profile.get("location")
    updated_profile["members"] = merge_members(user_profile.get("members", []), new_info.get("members", []))

    # Step 3: Handle greeting
    if intent == "greeting":
        return {
            "action": "static",
            "response": "Hello! How can I assist you today with your insurance needs?",
            "updated_profile": updated_profile,
            "updated_last_action": "greeting"
        }

    # Step 4: Handle passive intents
    if intent in ["concept_query", "policy_query", "limitation_query", "general_info"]:
        return {
            "action": "call_gpt",
            "response": None,
            "updated_profile": updated_profile,
            "updated_last_action": intent
        }

    # Step 5: Unknown intent
    if intent == "unknown":
# Step 5: Unknown intent (context-aware handling)
    # Case A: Profile incomplete → push to ask_info
        if not is_profile_complete(updated_profile):
            return {
                "action": "ask_info",
                "response": None,  # handled later by GPT or deterministic mapping
                "updated_profile": updated_profile,
                "updated_last_action": "ask_info"
            }

        # Case B: Last action was recommend → assume user wants clarification or comparison
        if last_bot_action == "recommend":
            return {
                "action": "compare",
                "response": None,
                "updated_profile": updated_profile,
                "updated_last_action": "compare"
            }

        # Case C: Last action was greeting or static → nudge towards recommendation
        if last_bot_action in ["greeting", "static"]:
            return {
                "action": "recommend",
                "response": None,
                "updated_profile": updated_profile,
                "updated_last_action": "recommend"
            }

        # Case D: Default fallback
        return {
            "action": "static",
            "response": "I didn’t quite get that. Do you want me to explain terms, recommend plans, or help compare options?",
            "updated_profile": updated_profile,
            "updated_last_action": "unknown"
        }

    # Step 6a: Handle affirmation
    if intent == "affirmation":
        if is_profile_complete(updated_profile):
            return {
                "action": "recommend",
                "response": None,
                "updated_profile": updated_profile,
                "updated_last_action": "recommend"
            }
        else:
            return {
                "action": "ask_info",
                "response": None,  # let GPT generate the follow-up question
                "updated_profile": updated_profile,
                "updated_last_action": "ask_info"
            }

    # Step 6b: Handle profile_info (only when last bot asked for info)
    if intent == "profile_info" and last_bot_action == "ask_info":
        if is_profile_complete(updated_profile):
            return {
                "action": "recommend",
                "response": None,
                "updated_profile": updated_profile,
                "updated_last_action": "recommend"
            }
        else:
            return {
                "action": "ask_info",
                "response": None,  # GPT will decide next question
                "updated_profile": updated_profile,
                "updated_last_action": "ask_info"
            }

    # Step 7: Recommendation / Compare
    if intent in ["recommend", "compare"]:
        if is_profile_complete(updated_profile):
            return {
                "action": intent,
                "response": None,
                "updated_profile": updated_profile,
                "updated_last_action": intent
            }
        else:
            return {
                "action": "ask_info",
                "response": None,  # GPT will decide next question
                "updated_profile": updated_profile,
                "updated_last_action": "ask_info"
            }

    # Step 8: Fallback
    return {
        "action": "fallback",
        "response": "Sorry, I didn’t quite catch that. Could you rephrase?",
        "updated_profile": updated_profile,
        "updated_last_action": "fallback"
    }
