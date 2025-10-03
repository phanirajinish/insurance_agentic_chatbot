from core.dialogue_manager import handle_dialogue
from core.intent_handler import classify_intent
from core.gpt_handler import call_gpt
from core.scoring import score_plans_and_recommend
import textwrap

def missing_fields(profile):
    missing = []
    if not any(m.get("relation") == "self" and isinstance(m.get("age"), int) for m in profile.get("members", [])):
        missing.append("age")
    if not profile.get("gender"):
        missing.append("gender")
    if not profile.get("location"):
        missing.append("location")
    return missing

def run_chat_controller(user_input, user_profile, last_bot_action, total_tokens, total_cost_inr):
    # Step 1: Use existing user_profile (no GPT extraction now)
    updated_profile = dict(user_profile)

    # Step 2: Classify intent
    intent_obj = classify_intent(user_input)
    intent = intent_obj["output"]

    # Step 3: Dialogue manager
    result = handle_dialogue(
        user_input=user_input,
        user_profile=updated_profile,
        intent=intent,
        last_bot_action=last_bot_action
    )

    print('----------------------')
    print(user_input)
    print(intent)
    print(result)
    print('----------------------')

    # Step 4: Generate reply
    if result["action"] == "ask_info":
        miss = missing_fields(result["updated_profile"])
        system_prompt = """
        You are a smart and friendly health insurance advisor chatbot.
        Based on the user’s current profile and the missing fields list,
        ask one natural, conversational question to get one of the missing fields.
        Only ask for one field at a time.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Profile so far: {result['updated_profile']}\nMissing fields: {miss}"}
        ]
        gpt_response = call_gpt(messages)
        reply = gpt_response["output"]
        total_tokens += gpt_response["tokens_used"]
        total_cost_inr += gpt_response["cost_inr"]

    elif result["action"] == "recommend":
        recom_resp = score_plans_and_recommend(user_profile=updated_profile)

        # --- prepare score data ---
        score_fit = recom_resp.get("score_fit", {})
        score_fit_sorted = sorted(score_fit.items(), key=lambda x: x[1], reverse=True)

        # top 3 distinct plans
        seen = set()
        top3 = []
        for plan, score in score_fit_sorted:
            if plan not in seen:
                top3.append((plan, score))
                seen.add(plan)
            if len(top3) == 3:
                break

        # --- collect relevant needs from those top plans ---
        user_needs = []
        for plan, _ in top3:
            user_needs.extend(recom_resp.get("needs", {}).get(plan, []))
        user_needs = list(set(user_needs))

        # --- build system prompt ---
        system_prompt = textwrap.dedent(f"""
            You are an insurance advisor. Based on the data below, generate:
            1. A clear recommendation message (~150 words) highlighting the **single best plan**.
            - Show why this plan fits the user’s profile (refer to these needs: {user_needs}).
            - Mention Sum Insured and suggested term.
            2. Mention the **next 2 best alternatives** briefly.
            3. A comparison table (Markdown format) for the top 3 plans, with columns:
            - Plan Name
            - Score
            - Key Benefits (only the needs relevant to user profile: {user_needs})
            4. End with a short, friendly follow-up question that nudges the user towards action,
            such as:
            - connecting with an expert,
            - requesting a callback,
            - or exploring premium details.

            Recommendation data:
            Top 3 ranked plans: {top3}
            All scores: {score_fit}
            User attributes: {recom_resp.get('user_attributes')}
            Relevant needs: {user_needs}
            Suggested term: Suggest best term 1 / 2/ 3 years for this Profile
            Sum Insured: Infer best SI for this profile in Lakh
        """)

        # --- GPT call ---
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User intent: recommend. Question: {user_input}"}
        ]
        gpt_response = call_gpt(messages)

        reply = gpt_response["output"]
        total_tokens += gpt_response["tokens_used"]
        total_cost_inr += gpt_response["cost_inr"]

    elif result["action"] == "compare":
        reply = "Sure, I can help you compare top plans..."

    elif result["action"] == "static":
        reply = result["response"]

    elif result["action"] == "call_gpt":
        system_prompt = """
        You are a helpful health insurance advisor. 
        - ONLY talk about Health Insurance (ignore other types like auto, life etc.).
        - Be clear, friendly, and factual.
        - Return answers ONLY as neat bullet points and concise.
        - Limit to max 5 points.
        - Always give the follow-up question or next step to be truly conversational.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User intent: {intent}. Question: {user_input}"}
        ]
        gpt_response = call_gpt(messages)
        reply = gpt_response["output"]
        total_tokens += gpt_response["tokens_used"]
        total_cost_inr += gpt_response["cost_inr"]

    elif result["action"] == "fallback":
        reply = result["response"]

    else:
        reply = "Let me connect you to a human advisor."

    return {
        "reply": reply,
        "action": result.get("action", "static"),
        "updated_profile": result["updated_profile"],
        "updated_last_action": result["updated_last_action"],
        "total_tokens": total_tokens,
        "total_cost_inr": total_cost_inr
    }
