"""
Matrix-Based Recommendation Engine for Insurance Plans

This module implements a sophisticated recommendation system using matrix multiplication:
- Matrix 1: User Attributes → Insurance Needs (what features user needs)
- Matrix 2: Insurance Needs → Policies (which policies have those features)
- Result: User Attributes → Policy Scores (by matrix multiplication)
"""

import numpy as np
import pandas as pd
import json
import os
from typing import Dict, List, Tuple

# Load knowledge base
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
KB_PATH = os.path.join(DATA_DIR, "knowledge_base_merged.json")

with open(KB_PATH, "r") as f:
    knowledge_base = json.load(f)


# ============================================================================
# USER ATTRIBUTES → INSURANCE NEEDS MATRIX (Matrix 1)
# ============================================================================

# Define user attribute categories
USER_ATTRIBUTES = [
    # Demographics
    "young_adult_18_30",
    "adult_31_45",
    "middle_aged_46_60",
    "senior_60_plus",
    "female",
    "male",
    
    # Family structure
    "single",
    "married",
    "has_children",
    "has_parents",
    
    # Health
    "has_chronic_conditions",
    "diabetic",
    "hypertensive",
    "respiratory_issues",
    "healthy",
    
    # Location
    "metro_city",
    "tier2_city",
    "tier3_city",
    
    # Financial
    "budget_conscious",
    "mid_range",
    "premium_seeker",
]

# Define insurance needs/features
INSURANCE_NEEDS = [
    # Core Coverage
    "high_sum_insured",
    "room_rent_flexibility",
    "no_copay",
    "unlimited_restore",
    
    # Specific Needs
    "maternity_coverage",
    "ped_coverage_quick",
    "parent_coverage",
    "child_coverage",
    
    # Additional Benefits
    "wellness_benefits",
    "consumables_cover",
    "air_ambulance",
    "unlimited_sum_insured",
    
    # Modern Healthcare
    "ayush_coverage",
    "mental_health",
    "home_care_treatment",
    "telemedicine",
    
    # Waiting Periods
    "low_waiting_periods",
    "quick_ped_waiver",
    
    # Value Add
    "no_claim_bonus",
    "lifelong_renewability",
    "comprehensive_network",
]

# Matrix 1: User Attributes → Insurance Needs
# Shape: (len(USER_ATTRIBUTES), len(INSURANCE_NEEDS))
def build_user_needs_matrix():
    """
    Build the matrix mapping user attributes to insurance needs.
    Each cell represents how important a need is for a given user attribute (0-1 scale)
    """
    matrix = np.zeros((len(USER_ATTRIBUTES), len(INSURANCE_NEEDS)))
    
    # Create DataFrame for easier indexing
    df = pd.DataFrame(matrix, index=USER_ATTRIBUTES, columns=INSURANCE_NEEDS)
    
    # ========== DEMOGRAPHICS ==========
    
    # Young Adults (18-30): Modern features, wellness, digital-first
    # Aspire/Elevate type plans - modern, feature-rich
    df.loc["young_adult_18_30", ["wellness_benefits", "telemedicine", "no_claim_bonus"]] = [0.9, 0.9, 0.9]
    df.loc["young_adult_18_30", ["high_sum_insured", "lifelong_renewability", "consumables_cover"]] = [0.7, 0.8, 0.6]
    
    # Adults (31-45): Family coverage, maternity, comprehensive
    # Aspire/Care/Super Star for families
    df.loc["adult_31_45", ["high_sum_insured", "maternity_coverage", "child_coverage"]] = [0.9, 0.9, 0.8]
    df.loc["adult_31_45", ["no_copay", "unlimited_restore", "room_rent_flexibility"]] = [0.8, 0.8, 0.7]
    df.loc["adult_31_45", ["wellness_benefits", "telemedicine"]] = [0.7, 0.7]
    
    # Middle Aged (46-60): Transition to senior plans, PED important
    # ReAssure/Optima Secure - pre-senior focused
    df.loc["middle_aged_46_60", ["ped_coverage_quick", "quick_ped_waiver", "no_copay"]] = [0.9, 0.9, 0.9]
    df.loc["middle_aged_46_60", ["high_sum_insured", "parent_coverage", "comprehensive_network"]] = [0.9, 0.7, 0.8]
    df.loc["middle_aged_46_60", ["home_care_treatment"]] = [0.6]
    
    # Seniors (60+): Maximum PED coverage, comprehensive care
    # ReAssure/Optima Secure - senior-focused plans
    df.loc["senior_60_plus", ["ped_coverage_quick", "quick_ped_waiver", "unlimited_sum_insured"]] = [1.0, 1.0, 1.0]
    df.loc["senior_60_plus", ["no_copay", "home_care_treatment", "comprehensive_network"]] = [0.9, 0.9, 0.9]
    df.loc["senior_60_plus", ["parent_coverage", "air_ambulance"]] = [1.0, 0.8]
    
    # ========== GENDER SPECIFIC ==========
    
    # Female: Maternity, women care
    df.loc["female", ["maternity_coverage", "wellness_benefits"]] = [0.9, 0.8]
    
    # Male: Standard coverage
    df.loc["male", ["high_sum_insured", "no_claim_bonus"]] = [0.7, 0.7]
    
    # ========== FAMILY STRUCTURE ==========
    
    # Single: Individual coverage
    df.loc["single", ["no_claim_bonus", "wellness_benefits", "telemedicine"]] = [0.8, 0.7, 0.8]
    
    # Married: Family coverage, maternity
    df.loc["married", ["maternity_coverage", "high_sum_insured", "no_copay"]] = [0.8, 0.9, 0.8]
    
    # Has Children: Comprehensive family coverage
    df.loc["has_children", ["child_coverage", "high_sum_insured", "unlimited_restore"]] = [1.0, 0.9, 0.8]
    df.loc["has_children", ["room_rent_flexibility", "ayush_coverage"]] = [0.7, 0.6]
    
    # Has Parents: Senior coverage, PED
    df.loc["has_parents", ["parent_coverage", "ped_coverage_quick", "quick_ped_waiver"]] = [1.0, 0.9, 0.9]
    df.loc["has_parents", ["home_care_treatment", "air_ambulance"]] = [0.8, 0.7]
    
    # ========== HEALTH CONDITIONS ==========
    
    # Has Chronic Conditions: PED coverage priority
    df.loc["has_chronic_conditions", ["ped_coverage_quick", "quick_ped_waiver", "low_waiting_periods"]] = [1.0, 1.0, 1.0]
    df.loc["has_chronic_conditions", ["comprehensive_network", "home_care_treatment"]] = [0.9, 0.8]
    
    # Specific conditions
    df.loc["diabetic", ["ped_coverage_quick", "quick_ped_waiver", "wellness_benefits"]] = [1.0, 1.0, 0.8]
    df.loc["hypertensive", ["ped_coverage_quick", "quick_ped_waiver", "comprehensive_network"]] = [1.0, 1.0, 0.8]
    df.loc["respiratory_issues", ["ped_coverage_quick", "ayush_coverage", "home_care_treatment"]] = [1.0, 0.7, 0.8]
    
    # Healthy: Preventive care
    df.loc["healthy", ["wellness_benefits", "no_claim_bonus", "telemedicine"]] = [0.9, 0.9, 0.8]
    
    # ========== LOCATION ==========
    
    # Metro: More options, higher costs
    df.loc["metro_city", ["comprehensive_network", "air_ambulance", "telemedicine"]] = [0.9, 0.7, 0.8]
    
    # Tier 2/3: Cost-effective, essential coverage
    df.loc["tier2_city", ["high_sum_insured", "no_copay", "lifelong_renewability"]] = [0.8, 0.8, 0.8]
    df.loc["tier3_city", ["high_sum_insured", "no_copay", "lifelong_renewability"]] = [0.8, 0.9, 0.8]
    
    # ========== FINANCIAL ==========
    
    # Budget Conscious: Value for money
    df.loc["budget_conscious", ["high_sum_insured", "no_claim_bonus", "lifelong_renewability"]] = [0.8, 0.9, 0.8]
    
    # Mid Range: Balanced coverage
    df.loc["mid_range", ["high_sum_insured", "unlimited_restore", "wellness_benefits"]] = [0.8, 0.8, 0.8]
    df.loc["mid_range", ["maternity_coverage", "consumables_cover"]] = [0.7, 0.7]
    
    # Premium Seeker: All bells and whistles
    df.loc["premium_seeker", ["unlimited_sum_insured", "no_copay", "air_ambulance"]] = [1.0, 1.0, 0.9]
    df.loc["premium_seeker", ["consumables_cover", "mental_health", "wellness_benefits"]] = [0.9, 0.8, 0.9]
    
    return df.values


# ============================================================================
# INSURANCE NEEDS → POLICIES MATRIX (Matrix 2)
# ============================================================================

def extract_policy_features(policy_data: Dict) -> Dict[str, float]:
    """
    Extract features from a policy and map to insurance needs.
    Returns a dictionary mapping need → score (0-1)
    """
    features = {need: 0.0 for need in INSURANCE_NEEDS}
    
    # Get first variant (or aggregate across variants)
    if not policy_data.get("variants"):
        return features
    
    variant = policy_data["variants"][0]  # Use first variant
    
    # Extract coverage items
    coverage = variant.get("coverage", [])
    coverage_text = " ".join([str(c).lower() for c in coverage])
    
    # Extract riders
    riders = variant.get("riders", [])
    rider_text = " ".join([r.get("description", "").lower() for r in riders])
    
    # Extract sum insured options
    si_options = variant.get("sum_insured_options", [])
    
    # Combined text for searching
    all_text = coverage_text + " " + rider_text
    
    # ========== MAP FEATURES TO NEEDS ==========
    
    # High Sum Insured
    if any("1cr" in si or "unlimited" in si.lower() for si in si_options):
        features["high_sum_insured"] = 1.0
        features["unlimited_sum_insured"] = 1.0
    elif any("50l" in si or "25l" in si for si in si_options):
        features["high_sum_insured"] = 0.8
    
    # Room Rent
    if "any room" in coverage_text or "no room rent" in all_text:
        features["room_rent_flexibility"] = 1.0
    elif "room rent" in coverage_text:
        features["room_rent_flexibility"] = 0.5
    
    # Co-payment
    eligibility = variant.get("eligibility", {})
    copay = eligibility.get("co_payment", "").lower()
    if "not applicable" in copay or "nil" in copay or "no" in copay:
        features["no_copay"] = 1.0
    
    # Restore/Reload
    if "unlimited restore" in all_text or "reload" in all_text:
        features["unlimited_restore"] = 1.0
    elif "restore" in all_text:
        features["unlimited_restore"] = 0.7
    
    # Maternity
    if "maternity" in all_text:
        features["maternity_coverage"] = 1.0
        features["child_coverage"] = 0.8
    
    # PED Coverage
    if "ped" in all_text or "pre-existing" in all_text:
        features["ped_coverage_quick"] = 0.7
    if "quick shield" in all_text or "ped waiver" in all_text:
        features["quick_ped_waiver"] = 1.0
        features["ped_coverage_quick"] = 1.0
    if "waiting" in all_text and ("reduce" in all_text or "waive" in all_text):
        features["low_waiting_periods"] = 0.8
    
    # Wellness & Preventive
    if "wellness" in all_text or "health check" in all_text:
        features["wellness_benefits"] = 0.8
    
    # Consumables
    if "consumable" in all_text:
        features["consumables_cover"] = 1.0
    
    # Air Ambulance
    if "air ambulance" in all_text:
        features["air_ambulance"] = 1.0
    
    # AYUSH
    if "ayush" in all_text:
        features["ayush_coverage"] = 1.0
    
    # Mental Health
    if "mental" in all_text or "psychiatric" in all_text:
        features["mental_health"] = 1.0
    
    # Home Care
    if "home care" in all_text or "domiciliary" in all_text:
        features["home_care_treatment"] = 1.0
    
    # Telemedicine
    if "tele" in all_text or "online consultation" in all_text:
        features["telemedicine"] = 1.0
    
    # No Claim Bonus
    if "bonus" in all_text and ("no claim" in all_text or "ncb" in all_text):
        features["no_claim_bonus"] = 1.0
    
    # Lifelong Renewability
    if "lifelong" in all_text or "lifetime" in all_text:
        features["lifelong_renewability"] = 1.0
    
    # Network
    if "network" in all_text:
        features["comprehensive_network"] = 0.7
    
    # Parent Coverage (age limits)
    entry_age = eligibility.get("entry_age_individual", "")
    if "any age" in entry_age.lower() or "99" in entry_age or "no limit" in entry_age.lower():
        features["parent_coverage"] = 1.0
    elif "70" in entry_age or "80" in entry_age:
        features["parent_coverage"] = 0.8
    
    return features


def build_needs_policies_matrix() -> Tuple[np.ndarray, List[str]]:
    """
    Build the matrix mapping insurance needs to policies.
    
    Returns:
        matrix: Shape (len(INSURANCE_NEEDS), len(policies))
        policy_names: List of policy names
    """
    policies = knowledge_base.get("policies", [])
    
    matrix = np.zeros((len(INSURANCE_NEEDS), len(policies)))
    policy_names = []
    
    for idx, policy in enumerate(policies):
        policy_name = policy.get("name", "Unknown")
        insurer = policy.get("insurer", "")
        policy_names.append(f"{policy_name} ({insurer})")
        
        # Extract features
        features = extract_policy_features(policy)
        
        # Fill column
        for need_idx, need in enumerate(INSURANCE_NEEDS):
            matrix[need_idx, idx] = features[need]
    
    return matrix, policy_names


# ============================================================================
# RECOMMENDATION ENGINE
# ============================================================================

def convert_profile_to_attributes(user_profile: Dict) -> np.ndarray:
    """
    Convert user profile to attribute vector.
    
    Returns:
        Vector of shape (len(USER_ATTRIBUTES),)
    """
    attributes = np.zeros(len(USER_ATTRIBUTES))
    attr_dict = dict(zip(USER_ATTRIBUTES, range(len(USER_ATTRIBUTES))))
    
    # Extract age (from self member)
    age = 30  # default
    for member in user_profile.get("members", []):
        if member.get("relation") == "self":
            age = member.get("age", 30)
            break
    
    # Age categories
    if 18 <= age <= 30:
        attributes[attr_dict["young_adult_18_30"]] = 1
    elif 31 <= age <= 45:
        attributes[attr_dict["adult_31_45"]] = 1
    elif 46 <= age <= 60:
        attributes[attr_dict["middle_aged_46_60"]] = 1
    else:
        attributes[attr_dict["senior_60_plus"]] = 1
    
    # Gender
    gender = user_profile.get("gender", "male").lower()
    if gender == "female":
        attributes[attr_dict["female"]] = 1
    else:
        attributes[attr_dict["male"]] = 1
    
    # Family structure
    relations = [m.get("relation") for m in user_profile.get("members", [])]
    if len(relations) == 1 and "self" in relations:
        attributes[attr_dict["single"]] = 1
    if any(r in ["wife", "husband", "spouse"] for r in relations):
        attributes[attr_dict["married"]] = 1
    if any(r in ["son", "daughter", "child"] for r in relations):
        attributes[attr_dict["has_children"]] = 1
    if any(r in ["father", "mother", "parent"] for r in relations):
        attributes[attr_dict["has_parents"]] = 1
    
    # Health conditions
    ped_conditions = user_profile.get("ped_conditions", [])
    if ped_conditions:
        attributes[attr_dict["has_chronic_conditions"]] = 1
        for condition in ped_conditions:
            condition_lower = condition.lower()
            if "diabet" in condition_lower:
                attributes[attr_dict["diabetic"]] = 1
            if "hypertension" in condition_lower or "bp" in condition_lower:
                attributes[attr_dict["hypertensive"]] = 1
            if "asthma" in condition_lower or "copd" in condition_lower or "respiratory" in condition_lower:
                attributes[attr_dict["respiratory_issues"]] = 1
    else:
        attributes[attr_dict["healthy"]] = 1
    
    # Location
    location = user_profile.get("location", "Tier 1").lower()
    if "tier 1" in location or "metro" in location:
        attributes[attr_dict["metro_city"]] = 1
    elif "tier 2" in location:
        attributes[attr_dict["tier2_city"]] = 1
    else:
        attributes[attr_dict["tier3_city"]] = 1
    
    # Financial (inferred from age and family)
    if age < 30:
        attributes[attr_dict["budget_conscious"]] = 0.7
    elif age < 50:
        attributes[attr_dict["mid_range"]] = 0.7
    else:
        attributes[attr_dict["premium_seeker"]] = 0.5
    
    return attributes


def get_matrix_recommendations(user_profile: Dict, top_n: int = 5) -> Dict:
    """
    Get recommendations using matrix multiplication.
    
    Returns:
        Dictionary with scores, needs, and top policies
    """
    # Build matrices
    user_needs_matrix = build_user_needs_matrix()  # (attributes, needs)
    needs_policies_matrix, policy_names = build_needs_policies_matrix()  # (needs, policies)
    
    # Convert user profile to attribute vector
    user_attributes = convert_profile_to_attributes(user_profile)  # (attributes,)
    
    # Matrix multiplication: user_attributes @ user_needs_matrix → user_needs
    user_needs = user_attributes @ user_needs_matrix  # (needs,)
    
    # BOOST needs based on explicit user responses (sequential profiling)
    needs_dict = dict(zip(INSURANCE_NEEDS, range(len(INSURANCE_NEEDS))))
    
    # If user explicitly said YES to these features, boost the corresponding need score
    if user_profile.get("planning_maternity"):
        if "maternity_coverage" in needs_dict:
            user_needs[needs_dict["maternity_coverage"]] += 3.0  # Strong boost
    
    if user_profile.get("needs_opd"):
        if "wellness_benefits" in needs_dict:
            user_needs[needs_dict["wellness_benefits"]] += 2.0
    
    if user_profile.get("needs_critical_illness"):
        # Critical illness is usually a separate rider, but affects comprehensive coverage preference
        if "high_sum_insured" in needs_dict:
            user_needs[needs_dict["high_sum_insured"]] += 1.5
    
    if user_profile.get("needs_home_care"):
        if "home_care_treatment" in needs_dict:
            user_needs[needs_dict["home_care_treatment"]] += 2.5
        if "parent_coverage" in needs_dict:
            user_needs[needs_dict["parent_coverage"]] += 1.0
    
    if user_profile.get("uses_ayush"):
        if "ayush_coverage" in needs_dict:
            user_needs[needs_dict["ayush_coverage"]] += 2.0
    
    if user_profile.get("travels_frequently"):
        if "air_ambulance" in needs_dict:
            user_needs[needs_dict["air_ambulance"]] += 2.5
        if "comprehensive_network" in needs_dict:
            user_needs[needs_dict["comprehensive_network"]] += 1.0
    
    if user_profile.get("prefers_wellness"):
        if "wellness_benefits" in needs_dict:
            user_needs[needs_dict["wellness_benefits"]] += 2.5
        if "telemedicine" in needs_dict:
            user_needs[needs_dict["telemedicine"]] += 2.0
    
    if user_profile.get("needs_accident_cover"):
        # Accident coverage affects comprehensive network and coverage preferences
        if "comprehensive_network" in needs_dict:
            user_needs[needs_dict["comprehensive_network"]] += 1.0
    
    if user_profile.get("needs_hospital_cash"):
        # Hospital cash is a rider, but indicates preference for value-added benefits
        if "wellness_benefits" in needs_dict:
            user_needs[needs_dict["wellness_benefits"]] += 0.5
    
    if user_profile.get("needs_mental_health"):
        if "mental_health" in needs_dict:
            user_needs[needs_dict["mental_health"]] += 2.5
    
    # Matrix multiplication: user_needs @ needs_policies_matrix → policy_scores
    policy_scores = user_needs @ needs_policies_matrix  # (policies,)
    
    # Normalize scores to 1-5 scale with REDUCED GAP between policies
    if policy_scores.max() > 0:
        # Min-max normalization to narrower range (3.5-5.0) to reduce gap
        # This makes all top policies appear competitive while maintaining ranking
        min_score = policy_scores.min()
        max_score = policy_scores.max()
        if max_score > min_score:
            # Map to 3.5-5.0 range (gap of only 1.5 instead of 4)
            policy_scores = 3.5 + ((policy_scores - min_score) / (max_score - min_score)) * 1.5
        else:
            policy_scores = np.full_like(policy_scores, 4.2)  # Default to high middle score
    
    # Create results dictionary
    results = {
        "policy_names": policy_names,
        "scores": policy_scores.tolist(),
        "user_attributes": USER_ATTRIBUTES,
        "user_attribute_values": user_attributes.tolist(),
        "insurance_needs": INSURANCE_NEEDS,
        "user_need_scores": user_needs.tolist(),
    }
    
    # Get top N with explanations
    top_indices = np.argsort(policy_scores)[::-1][:top_n]
    results["top_policies"] = []
    
    for i, idx in enumerate(top_indices):
        policy = policy_names[idx]
        score = float(policy_scores[idx])
        
        # Find which needs contributed most to this policy's score
        policy_features = needs_policies_matrix[:, idx]  # Features this policy has
        need_contributions = user_needs * policy_features  # Element-wise: user need × policy has it
        
        # Get top contributing needs (increased from 5 to 8 for more benefits)
        top_need_indices = np.argsort(need_contributions)[::-1][:8]
        contributing_needs = [
            {
                "need": INSURANCE_NEEDS[need_idx],
                "contribution": float(need_contributions[need_idx])
            }
            for need_idx in top_need_indices
            if need_contributions[need_idx] > 0
        ]
        
        results["top_policies"].append({
            "rank": i + 1,
            "policy": policy,
            "score": score,
            "why_recommended": contributing_needs[:5]  # Top 5 reasons (increased from 3)
        })
    
    # Get top needs for user
    top_need_indices = np.argsort(user_needs)[::-1][:10]
    results["top_needs"] = [
        {
            "need": INSURANCE_NEEDS[idx],
            "score": float(user_needs[idx])
        }
        for idx in top_need_indices if user_needs[idx] > 0
    ]
    
    return results

