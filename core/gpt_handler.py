from openai import OpenAI
import streamlit as st

COSTS = {
    "gpt-4o-mini": {
        "input": 0.00015,
        "output": 0.00060 
    },
    "gpt-4o": {
        "input": 5.00 / 1000,
        "output": 15.00 / 1000
    }
}

def call_gpt(messages, model="gpt-4o-mini", temperature=0):
    """
    GPT call wrapper with cost + token tracking.
    API key is fetched securely from Streamlit secrets.
    """
    if model not in COSTS:
        raise ValueError(f"Unsupported model: {model}")

    api_key = st.secrets["openai"]["api_key"]
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=500
    )

    output = response.choices[0].message.content.strip()

    usage = response.usage
    input_tokens = usage.prompt_tokens
    output_tokens = usage.completion_tokens
    total_tokens = usage.total_tokens

    cost_usd = (
        (input_tokens / 1000) * COSTS[model]["input"]
        + (output_tokens / 1000) * COSTS[model]["output"]
    )
    cost_inr = cost_usd * 83

    return {
        "output": output,
        "tokens_used": total_tokens,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost_usd, 4),
        "cost_inr": round(cost_inr, 4)
    }
