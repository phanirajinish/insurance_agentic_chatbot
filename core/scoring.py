import pandas as pd
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH_v = os.path.join(BASE_DIR,"insurance_chatbot", "data", "df_variations.csv")
DATA_PATH_r = os.path.join(BASE_DIR,"insurance_chatbot", "data", "dfv_variations.parquet")

df_all = pd.read_csv(DATA_PATH_v)
df_rec = pd.read_parquet(DATA_PATH_r)


def convert_user_profile(raw_profile):
    profile_flags = {
        "male_below_35": 0,
        "female_below_35": 0,
        "male_35_to_45": 0,
        "female_35_to_45": 0,
        "male_46_60": 0,
        "female_46_60": 0,
        "male_above_60": 0,
        "female_above_60": 0,
        "city_tier_1": 0,
        "city_tier_2": 0,
        "city_tier_3": 0,
        "family_self": 0,
        "family_self_spouse": 0,
        "family_self_children": 0,
        "family_self_parents": 0,
        # "family_extended": 0,
        "chronic_condition": 0,
        "critical_illness_history": 0
    }

    # Gender + Age mapping (for self only)
    for member in raw_profile.get("members", []):
        if member["relation"] == "self":
            age = member["age"]
            gender = raw_profile["gender"]
            if gender == "male":
                if age < 35:
                    profile_flags["male_below_35"] = 1
                elif 35 <= age <= 45:
                    profile_flags["male_35_to_45"] = 1
                elif 46 <= age <= 60:
                    profile_flags["male_46_60"] = 1
                else:
                    profile_flags["male_above_60"] = 1
            elif gender == "female":
                if age < 35:
                    profile_flags["female_below_35"] = 1
                elif 35 <= age <= 45:
                    profile_flags["female_35_to_45"] = 1
                elif 46 <= age <= 60:
                    profile_flags["female_46_60"] = 1
                else:
                    profile_flags["female_above_60"] = 1

    # City tier mapping
    loc = raw_profile.get("location", "").lower()
    if "tier 1" in loc:
        profile_flags["city_tier_1"] = 1
    elif "tier 2" in loc:
        profile_flags["city_tier_2"] = 1
    elif "tier 3" in loc:
        profile_flags["city_tier_3"] = 1

    # Family structure
    relations = [m["relation"] for m in raw_profile.get("members", [])]
    if relations == ["self"]:
        profile_flags["family_self"] = 1
    elif "wife" in relations or "husband" in relations:
        profile_flags["family_self_spouse"] = 1
    elif any(r in ["son", "daughter", "child"] for r in relations):
        profile_flags["family_self_children"] = 1
    elif any(r in ["father", "mother", "parent"] for r in relations):
        profile_flags["family_self_parents"] = 1
    # elif len(relations) > 2:
    #     profile_flags["family_extended"] = 1

    # Health conditions → simple rule
    if len(raw_profile.get("ped_conditions", [])) > 0:
        profile_flags["chronic_condition"] = 1
        profile_flags["critical_illness_history"] = 1

    return pd.DataFrame([profile_flags])

def score_plans_and_recommend(user_profile):
    df_profile = convert_user_profile(user_profile)

    # df_all = df_all.drop_duplicates(subset=df_profile.columns.tolist())
    matches = np.all(df_all[df_profile.columns ].values == df_profile .values, axis=1)
    matching_indices = df_all.index[matches].tolist()[0]
    df_final = df_rec.loc[[matching_indices], :] 
    final_dict = df_final.sample(1) .to_dict() 




    return final_dict