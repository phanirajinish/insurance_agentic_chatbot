from core.gpt_handler import call_gpt

def gpt_profile_extractor(user_input: str, model="gpt-4o-mini") -> dict:
    system_prompt = """
    You are a profile extraction engine for a health insurance chatbot.
    Extract structured data from the user's message in the following JSON format:

    {
    "gender": "male" or "female" or null,
    "location": "Tier 1" / "Tier 2" / "Tier 3" or null,
    "members": [
        {"relation": "self/spouse/father/mother/son/daughter/...", "age": integer},
        ...
    ]
    }

    Strict rules:
    - Extract only what is *explicitly stated* in the message.
    - Do NOT assume gender or location. If not clearly mentioned, set them to null.
    - Age must be a number. If unclear, skip the member.
    - If a person is mentioned but no relation is stated, default to "self".
    - Never guess or hallucinate values.

    Only return valid JSON. No explanations or extra text.
    """


    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    response = call_gpt(messages, model=model, temperature=0)
    raw_output = response["output"]

    try:
        import json
        extracted = json.loads(raw_output)
    except Exception:
        extracted = {}

    return extracted
