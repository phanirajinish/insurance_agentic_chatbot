from core.profile_extractor import gpt_profile_extractor
from core.intent_handler import flow_suggest

REQUIRED_FIELDS = ["gender", "location", "members"]

def missing_fields(profile):
    missing = []
    if not any(m.get("relation") == "self" and isinstance(m.get("age"), int) and m["age"] >= 18
               for m in profile.get("members", [])):
        missing.append("age")
    if not profile.get("gender"):
        missing.append("gender")
    if not profile.get("location"):
        missing.append("location")
    return missing

def is_profile_complete(profile):
    """Return True if all required fields are present."""
    return len(missing_fields(profile)) == 0

def merge_members(existing, new):
    relation_map = {m['relation']: m for m in existing}
    for m in new:
        relation = m['relation']
        if relation in relation_map:
            if 'age' in m and m['age'] is not None:
                relation_map[relation]['age'] = m['age']
        else:
            relation_map[relation] = m
    return list(relation_map.values())

def handle_dialogue(user_input, user_profile, intent, last_bot_action, hop_count=0):
    # Step 1: extract + merge
    new_info = gpt_profile_extractor(user_input)
    updated_profile = dict(user_profile)
    updated_profile["gender"] = new_info.get("gender") or user_profile.get("gender")
    updated_profile["location"] = new_info.get("location") or user_profile.get("location")
    updated_profile["members"] = merge_members(user_profile.get("members", []), new_info.get("members", []))

    # -------------------------
    # Static / Simple Intents
    # -------------------------
    if intent == "greeting":
        return {
            "action": "static",
            "response": "Hello! 👋 I'm here to help you find the perfect health insurance plan from Apollo 24|7. Whether you want to explore different plans, get personalized recommendations, or learn about coverage options - I'm here for you! What would you like to know?",
            "updated_profile": updated_profile,
            "updated_last_action": "greeting",
            "flow_suggest": flow_suggest(intent, hop_count)
        }

    if intent == "goodbye":
        return {
            "action": "static",
            "response": "Thank you for exploring Apollo 24|7 health insurance with me! Feel free to come back anytime you need help. Stay healthy! 🛡️",
            "updated_profile": updated_profile,
            "updated_last_action": "goodbye"
        }

    if intent == "negation":
        return {
            "action": "static",
            "response": "No problem! I'm here whenever you're ready. Feel free to ask me anything about health insurance plans, coverage, or get personalized recommendations. What else can I help you with?",
            "updated_profile": updated_profile,
            "updated_last_action": "negation"
        }

    # -------------------------
    # Knowledge Lookup Intents (RAG-powered)
    # -------------------------
    knowledge_intents = [
        "policy_query", "rider_query", "limitation_query", "eligibility_query",
        "claims_query", "network_query", "concept_query", "catalog_info",
        "process_query", "renewal_query", "cancellation_query", "general_info"
    ]
    if intent in knowledge_intents:
        # These will be handled by RAG retrieval in chat_controller
        return {
            "action": "call_gpt",  # This triggers RAG in controller
            "response": None,
            "updated_profile": updated_profile,
            "updated_last_action": intent,
            "flow_suggest": flow_suggest(intent, hop_count)
        }

    # -------------------------
    # Affirmation Handling
    # -------------------------
    if intent == "affirmation":
        # Context-based behavior
        if last_bot_action == "concept_query":
            followup_context = (
                "The user said 'yes' after asking 'what is insurance'. "
                "Continue by explaining the main *types of health insurance plans in India*, "
                "such as individual, family floater, senior citizen, top-up, and critical illness policies. "
                "Use 4-5 concise bullet points and end with a question like "
                "'Would you like to know which type suits you best?'"
            )
            return {
                "action": "call_gpt",
                "response": followup_context,  # pass this to GPTHandler for contextual response
                "updated_profile": updated_profile,
                "updated_last_action": "concept_followup",
                "flow_suggest": flow_suggest("concept_followup", hop_count)
            }

        elif last_bot_action == "recommend":
            return {
                "action": "static",
                "response": "Great! I'm glad you found a plan that works for you. 🎉\n\nWould you like to:\n• See detailed premium breakdowns?\n• Compare this with other top plans?\n• Learn more about specific coverage features?\n• Connect with an advisor to finalize your policy?",
                "updated_profile": updated_profile,
                "updated_last_action": "recommend_followup"
            }
        elif last_bot_action == "ask_info":
            return {
                "action": "ask_info",
                "response": "Let's complete your profile to tailor the best plans for you.",
                "updated_profile": updated_profile,
                "updated_last_action": "ask_info",
                "flow_suggest": flow_suggest("ask_info", hop_count)
            }
        else:
            # Default: proceed to recommend if profile ready, else ask info
            if is_profile_complete(updated_profile):
                next_intent = "recommend"
            else:
                next_intent = "ask_info"
            return {
                "action": next_intent,
                "response": None,
                "updated_profile": updated_profile,
                "updated_last_action": next_intent,
                "flow_suggest": flow_suggest(next_intent, hop_count)
            }


    # -------------------------
    # Profile Update / Info Collection
    # -------------------------
    profile_update_intents = [
        "profile_info", "health_info", "insurer_preference",
        "sum_insured_preference", "budget_info", "term_preference"
    ]
    if intent in profile_update_intents:
        next_intent = "recommend" if is_profile_complete(updated_profile) else "ask_info"
        return {
            "action": next_intent,
            "response": None,
            "updated_profile": updated_profile,
            "updated_last_action": next_intent,
            "flow_suggest": flow_suggest(next_intent, hop_count)
        }

    # -------------------------
    # Recommendation / Engine Triggers
    # -------------------------
    if intent in ["recommend", "compare", "premium_quote"]:
        next_intent = intent if is_profile_complete(updated_profile) else "ask_info"
        return {
            "action": next_intent,
            "response": None,
            "updated_profile": updated_profile,
            "updated_last_action": next_intent,
            "flow_suggest": flow_suggest(next_intent, hop_count)
        }

    # -------------------------
    # Unknown / Fallback
    # -------------------------
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
<<<<<<< HEAD
            "response": "I didn't quite catch that, but I'm here to help! 😊\n\nI can assist you with:\n• Explaining insurance terms and concepts\n• Recommending the best plans for your needs\n• Comparing different policies\n• Answering questions about coverage, claims, and more\n\nWhat would you like to explore?",
=======
            "response": "I didn’t quite get that. Do you want me to explain terms, recommend plans, or help compare options?",
>>>>>>> ee9a3c77d6f49b5a64335a0d2194d3475cfbcb83
            "updated_profile": updated_profile,
            "updated_last_action": "unknown",
            "flow_suggest": flow_suggest("unknown", hop_count)
        }

    return {
        "action": "fallback",
        "response": "I'm not sure I understood that correctly. Could you rephrase your question? Or would you like me to help you explore our insurance plans instead?",
        "updated_profile": updated_profile,
        "updated_last_action": "fallback",
        "flow_suggest": flow_suggest("fallback", hop_count)
    }
