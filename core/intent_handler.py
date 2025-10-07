from core.gpt_handler import call_gpt


# ------------------------------------------------------
# 1. User Intent Classifier (GPT-driven, free-text input)
# ------------------------------------------------------
def classify_intent(user_input: str, model="gpt-4o-mini") -> str:
    """
    Classify the user's input into one of the predefined intents.
    Handles typos and variations robustly.
    """
    
    # Pre-process common typos and variations before GPT
    user_lower = user_input.lower().strip()
    
    # Catalog queries (MUST check BEFORE recommend to avoid profile collection)
    # These are general "what do you have" queries WITHOUT personalization
    catalog_patterns = [
        ('polic', 'have'), ('polic', 'offer'), ('polic', 'provide'),
        ('polic', 'sell'), ('polic', 'available'), ('polic', 'from'),
        ('plan', 'have'), ('plan', 'offer'), ('plan', 'provide'),
        ('plan', 'sell'), ('plan', 'available'), ('plan', 'from'),
        ('what polic', ''), ('show polic', ''), ('list polic', ''),
        ('tell polic', ''), ('all polic', ''), ('polic', 'there'),
        ('what plan', ''), ('show plan', ''), ('list plan', ''),
        ('tell plan', ''), ('all plan', ''), ('plan', 'there'),
        ('what insurers', ''), ('which insurers', ''),
        ('what companies', ''), ('which companies', '')
    ]
    
    # Check if it's a catalog query WITHOUT personalization words
    personalizing_words = ['me', 'my', 'for me', 'i ', 'i\'m']
    has_personalization = any(word in user_lower for word in personalizing_words)
    
    if not has_personalization:  # Only catalog if NOT personalized
        for pattern1, pattern2 in catalog_patterns:
            if pattern2:
                if pattern1 in user_lower and pattern2 in user_lower:
                    return {"output": "catalog_info", "tokens_used": 0, "cost_inr": 0}
            else:
                if pattern1 in user_lower:
                    return {"output": "catalog_info", "tokens_used": 0, "cost_inr": 0}
    
    # Premium variations (common typos and shortcuts)
    premium_keywords = ['premium', 'premum', 'prmium', 'primium', 'premiun', 
                       'price', 'cost', 'pricing', 'amount', 'payment', 
                       'how much', 'what cost', 'pay']
    if any(keyword in user_lower for keyword in premium_keywords):
        return {"output": "premium_quote", "tokens_used": 0, "cost_inr": 0}
    
    # Recommend variations (personalized queries)
    recommend_keywords = ['recommend', 'suggest', 'best plan for', 'which plan for', 
                         'help me choose', 'find plan for me', 'best for me']
    if any(keyword in user_lower for keyword in recommend_keywords):
        return {"output": "recommend", "tokens_used": 0, "cost_inr": 0}
    
    # Compare variations
    compare_keywords = ['compare', 'comparison', 'difference', 'versus', 'vs']
    if any(keyword in user_lower for keyword in compare_keywords):
        return {"output": "compare", "tokens_used": 0, "cost_inr": 0}
    
    # Affirmation variations
    if user_lower in ['yes', 'yeah', 'yep', 'yup', 'sure', 'ok', 'okay', 'correct', 'right']:
        return {"output": "affirmation", "tokens_used": 0, "cost_inr": 0}
    
    # Negation variations
    if user_lower in ['no', 'nope', 'nah', 'not interested', 'skip', 'later']:
        return {"output": "negation", "tokens_used": 0, "cost_inr": 0}
    
    # Policy interest (user mentions a specific policy name)
    policy_names = ['super star', 'reassure', 'aspire', 'optima secure', 
                   'elevate', 'care', 'optima', 'super']
    if any(policy in user_lower for policy in policy_names):
        # Check if it's a short response (likely answering "which plan interests you?")
        if len(user_lower.split()) <= 5:
            return {"output": "policy_query", "tokens_used": 0, "cost_inr": 0}

    system_prompt = """
    You are an intent classifier for a health insurance chatbot. 
    Classify the user's message into exactly one of these intents.

    ## Conversation Control
    1. greeting – greetings like "hi", "hello".
    2. affirmation – short positives like "yes", "okay".
    3. negation – negative/decline like "no", "not interested", "skip".
    4. goodbye – polite closing like "bye", "thank you".

    ## Profile Update
    5. profile_info – user shares demographics (age, gender, city, family members).
    6. health_info – mentions pre-existing conditions or lifestyle (e.g., diabetic, smoker).
    7. insurer_preference – specifies preferred insurer (ICICI, HDFC, Star).
    8. sum_insured_preference – specifies desired sum insured (e.g., 50L, 1Cr).
    9. budget_info – mentions affordability (cheap, expensive, premium).
    10. term_preference – specifies policy term (1 year, 3 years).

    ## Engine Trigger
    11. recommend – asks for best plan or suggestion.
    12. compare – asks to compare insurers or policies.
    13. premium_quote – asks about premium, price, or cost (ANY variation of premium/price/cost).

    ## Knowledge Lookup
    14. policy_query – asks about policy features (room rent, maternity, PED coverage).
    15. rider_query – asks about riders/add-ons (maternity rider, critical illness).
    16. limitation_query – asks about exclusions or what is not covered.
    17. eligibility_query – asks about eligibility (e.g., "can I buy at 65?", "am I eligible if diabetic?").
    18. claims_query – asks about claim process.
    19. network_query – asks about hospital network.
    20. concept_query – asks to explain insurance terms (copay, deductible).
    21. catalog_info – asks what the bot/platform offers, available policies, insurers, or its purpose.
    22. process_query – asks about process, documents, or steps.
    23. renewal_query – asks about renewals.
    24. cancellation_query – asks about cancellations/refunds.

    ## Fallback
    25. general_info – broad or vague insurance questions.
    26. unknown – anything else not covered above.

    IMPORTANT: Be lenient with typos and variations. "prmium", "primium", "premiun" all mean premium_quote.

    Return only the intent label, e.g., "recommend".
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    result = call_gpt(messages, model=model, temperature=0)
    return result 


# ------------------------------------------------------
# 2. Flow Suggestion Engine (Tree-first + GPT fallback)
# ------------------------------------------------------
def flow_suggest(previous_intent: str, hop_count: int = 0, model="gpt-4o-mini"):
    """
    Suggests next bot actions based on the last user intent.
    1. Uses a rule-based tree (safe, deterministic).
    2. Falls back to GPT if the intent is not in the tree.
    """

    print(previous_intent)

    # Closure rule
    if hop_count >= 3:
        return [
            {"text": "Would you like me to connect you with an advisor to finalize?", 
             "intent": "advisor_closure"}
        ]

    # Rule-based mapping (safe tree)
    mapping = {
        "greeting": [
            {"text": "I can recommend a plan tailored to you — shall we start?", "intent": "profile_info"},
            {"text": "Want to first explore available insurers?", "intent": "catalog_info"}
        ],
        "profile_info": [
            {"text": "Great, should I now recommend the best plan for you?", "intent": "recommend"},
            {"text": "Want to check premiums first?", "intent": "premium_quote"}
        ],
        "health_info": [
            {"text": "Should I recommend plans that suit your health profile?", "intent": "recommend"},
            {"text": "Or would you prefer to check premiums first?", "intent": "premium_quote"}
        ],
        "recommend": [
            {"text": "This plan is a strong match — want to see how much it costs for you?", "intent": "premium_quote"},
            {"text": "Or compare it with 2 others people like you consider?", "intent": "compare"}
        ],
        "compare": [
            {"text": "Curious to see the premium difference side by side?", "intent": "premium_quote"},
            {"text": "Want to know claim process for these options?", "intent": "claims_query"}
        ],
        "premium_quote": [
            {"text": "Would you like to know how quickly claims are settled?", "intent": "claims_query"},
            {"text": "Or should I guide you step-by-step on how to purchase?", "intent": "process_query"}
        ],
        "policy_query": [
            {"text": "That’s an important detail. Want me to compare this with other plans?", "intent": "compare"},
            {"text": "Or check premium if you include this rider?", "intent": "premium_quote"}
        ],
        "rider_query": [
            {"text": "Would you like to see how adding this rider changes premiums?", "intent": "premium_quote"},
            {"text": "Or compare plans that already include it?", "intent": "compare"}
        ],
        "limitation_query": [
            {"text": "Want me to show you which plans avoid this limitation?", "intent": "compare"},
            {"text": "Or check the premium differences for those plans?", "intent": "premium_quote"}
        ],
        "eligibility_query": [
            {"text": "Yes, you’re eligible. Shall I recommend plans in your range?", "intent": "recommend"},
            {"text": "Want a quick premium estimate?", "intent": "premium_quote"}
        ],
        "claims_query": [
            {"text": "Shall I recommend a plan that fits your needs?", "intent": "recommend"},
            {"text": "Want me to show premiums so you know the cost upfront?", "intent": "premium_quote"}
        ],
        "network_query": [
            {"text": "Want to see plans with the widest hospital coverage?", "intent": "compare"},
            {"text": "Or check premium estimates for your city?", "intent": "premium_quote"}
        ],
        "process_query": [
            {"text": "Would you like me to show you documents needed?", "intent": "process_query"},
            {"text": "Or guide you to buy the policy now?", "intent": "advisor_closure"}
        ],
        "renewal_query": [
            {"text": "Want me to show you easy-renewal plans?", "intent": "recommend"},
            {"text": "Or check renewal premiums?", "intent": "premium_quote"}
        ],
        "cancellation_query": [
            {"text": "Want to see refund rules across plans?", "intent": "compare"},
            {"text": "Or know premium refund timelines?", "intent": "process_query"}
        ],
    }

    if previous_intent in mapping:
        return {
            "output": mapping[previous_intent],
            "tokens_used": 0,
            "cost_inr": 0.0
        }

    # GPT fallback
    system_prompt = """
    You are a fallback flow suggestion engine for a health insurance chatbot.
    Suggest exactly 2 engaging next steps in JSON format:
    [
      {"text": "Bot message here", "intent": "intent_label"},
      {"text": "Another option", "intent": "intent_label"}
    ]
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Previous intent: {previous_intent}, Hop count: {hop_count}"}
    ]

    result = call_gpt(messages, model=model, temperature=0)

    # Return both the output and cost tracking information
    return {
        "output": result["output"],
        "tokens_used": result.get("tokens_used", 0),
        "cost_inr": result.get("cost_inr", 0.0)
    } 