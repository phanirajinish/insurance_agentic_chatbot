"""
Sequential Profile Builder - Asks health-related questions based on policy features

This module determines what additional questions to ask users based on:
1. What policy features are available (maternity, OPD, CI, etc.)
2. User demographics (age, gender, family structure)
3. What we haven't asked yet

Focuses ONLY on health-related needs, not financial/budget questions.
"""

from typing import Dict, List, Tuple, Optional


def get_next_profile_question(user_profile: Dict) -> Optional[Tuple[str, str, str]]:
    """
    Determine the next most relevant question to ask the user.
    
    Returns: (question_key, question_text, explanation) or None if profile is complete
    
    question_key: The profile field to update (e.g., "planning_maternity")
    question_text: The actual question to ask the user
    explanation: Why this matters (shown after their answer)
    """
    
    # Extract current profile data
    gender = user_profile.get("gender", "").lower()
    members = user_profile.get("members", [])
    ped_conditions = user_profile.get("ped_conditions", [])
    
    # Calculate demographics
    has_female_adult = any(
        m.get("relation") in ["self", "wife", "spouse"] and 
        m.get("age", 0) >= 20 and 
        m.get("age", 0) <= 40
        for m in members
    ) or (gender == "female" and any(m.get("relation") == "self" and 20 <= m.get("age", 0) <= 40 for m in members))
    
    has_children = any(m.get("relation") in ["son", "daughter", "child"] for m in members)
    has_parents = any(m.get("relation") in ["mother", "father", "parent"] for m in members)
    has_seniors = any(m.get("age", 0) >= 60 for m in members)
    has_chronic_conditions = len(ped_conditions) > 0
    
    youngest_age = min([m.get("age", 100) for m in members] + [100]) if members else 100
    
    
    # Priority order: Most impactful to least impactful
    # Each question maps to specific policy riders/features
    
    # 1. Maternity (High impact, time-sensitive)
    if "planning_maternity" not in user_profile and has_female_adult:
        return (
            "planning_maternity",
            "Are you or your spouse planning for pregnancy in the next 2-3 years? 🤰\n\n"
            "(This helps me recommend plans with maternity coverage and newborn benefits)",
            "Great! Policies with maternity riders typically have a 12-24 month waiting period, "
            "so it's important to get covered early."
        )
    
    # 2. OPD/Outpatient (Very common need)
    if "needs_opd" not in user_profile:
        return (
            "needs_opd",
            "Do you visit doctors regularly for consultations, medicines, or routine check-ups? 🏥\n\n"
            "(Most basic plans only cover hospitalization. OPD add-ons cover outpatient expenses)",
            "I'll look for plans with OPD/outpatient coverage to help with your day-to-day medical expenses."
        )
    
    # 3. Critical Illness (Important protection)
    if "needs_critical_illness" not in user_profile and youngest_age >= 25:
        return (
            "needs_critical_illness",
            "Would you like lump-sum protection against critical illnesses like cancer, stroke, or heart attack? 💔\n\n"
            "(This pays a one-time amount on diagnosis, independent of hospitalization costs)",
            "Critical illness riders provide financial cushion beyond medical expenses - great for income replacement."
        )
    
    # 4. Home Care (Relevant for seniors/chronic conditions)
    if "needs_home_care" not in user_profile and (has_seniors or has_chronic_conditions or has_parents):
        return (
            "needs_home_care",
            "Do you or your family members have conditions that might require home care treatment or nursing? 🏠\n\n"
            "(Useful for elderly parents, chronic conditions, or post-surgery recovery)",
            "I'll prioritize plans with strong home care and domiciliary treatment coverage."
        )
    
    # 5. AYUSH/Alternative Medicine
    if "uses_ayush" not in user_profile:
        return (
            "uses_ayush",
            "Do you use alternative medicine like Ayurveda, Homeopathy, Yoga therapy, or Naturopathy? 🌿\n\n"
            "(All plans cover AYUSH, but some have better coverage limits)",
            "I'll ensure your plan has comprehensive AYUSH coverage for alternative treatments."
        )
    
    # 6. Travel/Air Ambulance (Relevant for frequent travelers)
    if "travels_frequently" not in user_profile:
        return (
            "travels_frequently",
            "Do you travel frequently or live far from major hospitals? ✈️\n\n"
            "(Air ambulance coverage is crucial for emergencies when time matters)",
            "I'll look for plans with air ambulance coverage for emergency medical transport."
        )
    
    # 7. Wellness/Telemedicine (Modern healthcare preference)
    if "prefers_wellness" not in user_profile and youngest_age <= 45:
        return (
            "prefers_wellness",
            "Do you prefer plans with modern benefits like telemedicine, health checkups, and wellness rewards? 📱\n\n"
            "(Great for preventive care and convenience)",
            "I'll recommend plans with strong wellness programs and digital health services."
        )
    
    # 8. Personal Accident (Relevant for active individuals)
    if "needs_accident_cover" not in user_profile and youngest_age <= 50:
        return (
            "needs_accident_cover",
            "Do you need personal accident protection beyond health insurance? 🚗\n\n"
            "(Covers accidental death and disability - useful for breadwinners)",
            "I'll include plans with strong personal accident riders for comprehensive protection."
        )
    
    # 9. Hospital Cash (Income replacement)
    if "needs_hospital_cash" not in user_profile:
        return (
            "needs_hospital_cash",
            "Would daily cash benefits during hospitalization help cover other expenses? 💰\n\n"
            "(₹1,000-₹4,000 per day to cover lost income, travel, food, etc.)",
            "Hospital cash riders provide extra financial cushion during hospitalization."
        )
    
    # 10. Mental Health (Modern need)
    if "needs_mental_health" not in user_profile and youngest_age <= 55:
        return (
            "needs_mental_health",
            "Would you like coverage for mental health counseling, therapy, or psychiatric care? 🧠\n\n"
            "(Growing importance of mental health coverage in modern plans)",
            "I'll look for plans with mental health benefits - it's becoming increasingly important."
        )
    
    # All questions asked!
    return None


def parse_yes_no_response(user_input: str) -> Optional[bool]:
    """
    Parse user's response to yes/no questions.
    Returns: True (yes), False (no), or None (unclear)
    """
    user_lower = user_input.lower().strip()
    
    # Affirmative
    if any(word in user_lower for word in ["yes", "yeah", "yup", "sure", "definitely", "absolutely", "of course", "correct", "right", "ok", "okay"]):
        return True
    
    # Negative
    if any(word in user_lower for word in ["no", "nope", "nah", "not really", "don't need", "not interested", "skip", "later", "unnecessary"]):
        return False
    
    # Unclear
    return None


def get_profile_completion_status(user_profile: Dict) -> Dict:
    """
    Check profile completion status.
    Returns: {
        "basic_complete": bool,      # Gender, age, members
        "health_complete": bool,      # PEDs
        "needs_complete": bool,       # All sequential questions
        "completion_percentage": int  # 0-100
    }
    """
    
    # Basic demographics
    has_gender = "gender" in user_profile
    has_location = "location" in user_profile
    has_members = len(user_profile.get("members", [])) > 0
    basic_complete = has_gender and has_location and has_members
    
    # Health info
    health_complete = "ped_conditions" in user_profile
    
    # Sequential needs (10 possible questions)
    needs_fields = [
        "planning_maternity",
        "needs_opd",
        "needs_critical_illness",
        "needs_home_care",
        "uses_ayush",
        "travels_frequently",
        "prefers_wellness",
        "needs_accident_cover",
        "needs_hospital_cash",
        "needs_mental_health",
    ]
    
    # Count how many need fields are present
    needs_answered = sum(1 for field in needs_fields if field in user_profile)
    
    # Determine if we should ask more questions based on demographics
    # (Not all questions are relevant for everyone)
    total_questions = 0
    if basic_complete and health_complete:
        next_q = get_next_profile_question(user_profile)
        if next_q is None:
            total_questions = needs_answered  # All relevant questions answered
        else:
            total_questions = needs_answered + 1  # More to go
    else:
        total_questions = 10  # Default max
    
    needs_complete = (next_q is None) if (basic_complete and health_complete) else False
    
    # Calculate completion percentage
    basic_weight = 40  # 40% for basic demographics
    health_weight = 20  # 20% for PEDs
    needs_weight = 40   # 40% for sequential needs
    
    completion = 0
    if basic_complete:
        completion += basic_weight
    if health_complete:
        completion += health_weight
    if needs_complete:
        completion += needs_weight
    elif total_questions > 0:
        completion += int((needs_answered / total_questions) * needs_weight)
    
    return {
        "basic_complete": basic_complete,
        "health_complete": health_complete,
        "needs_complete": needs_complete,
        "completion_percentage": min(completion, 100),
        "needs_answered": needs_answered,
        "total_needs": total_questions,
    }


def should_ask_more_questions(user_profile: Dict, action_requested: str) -> bool:
    """
    Determine if we should ask more profile questions before proceeding with action.
    
    Args:
        user_profile: Current user profile
        action_requested: What user wants to do ("recommend", "compare", "premium_quote")
    
    Returns: True if we should collect more info first, False if we can proceed
    """
    
    status = get_profile_completion_status(user_profile)
    
    # Always need basic info
    if not status["basic_complete"]:
        return True
    
    # For premium quotes, we need complete basic + health info
    if action_requested == "premium_quote":
        if not status["health_complete"]:
            return True
        # Don't need all needs questions for premium
        return False
    
    # For recommendations, we want at least some needs info
    # BUT don't force questions if user explicitly wants recommendations
    if action_requested in ["recommend", "compare"]:
        # If they have basic info, allow recommendations
        # Don't force sequential questions - they're optional enhancements
        return False
    
    # For other actions, basic + health is enough
    return not status["health_complete"]


# Export functions
__all__ = [
    "get_next_profile_question",
    "parse_yes_no_response",
    "get_profile_completion_status",
    "should_ask_more_questions",
]

