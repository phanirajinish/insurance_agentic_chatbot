from openai import OpenAI
import os
from core.gpt_handler import call_gpt



def classify_intent(user_input: str, model="gpt-4o-mini"):
    system_prompt = """
    You are an intent classifier for a health insurance chatbot. Classify the user's message into one of these intents:

    1. greeting – greetings like "hi", "hello", etc.
    2. profile_info – user gives info like age, gender, city, or family members. Even single words like "male", "30", or "Bangalore" should be profile_info.
    3. recommend – asks for plan suggestions or best policy.
    4. policy_query – asks about specific plan features (e.g., maternity, room rent).
    5. concept_query – asks to explain insurance terms (e.g., co-pay, deductible).
    6. compare – asks to compare policies or insurers.
    7. limitation_query – asks about exclusions or what’s not covered.
    8. affirmation – short positive replies like "yes", "okay", "sure", "go ahead".
    9. general_info – user wants to know about insurance in general, or asks vague/broad questions (e.g., “I want to know about insurance”).
    10. unknown – anything else.

    Return only the intent label (e.g., "profile_info").
    """


    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    result = call_gpt(messages, model=model, temperature=0)
    return result