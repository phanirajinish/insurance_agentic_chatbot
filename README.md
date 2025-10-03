1. User input → CLI (app.py).
2. Intent classification (intent_handler.py).
3. Dialogue manager checks profile completeness.
    If missing info → ask conversationally.
4. Scoring engine ranks policies for recommendation.
5. Retrieval engine fetches facts & concept explainers.
6. LLM handler blends:
    Scores (deterministic)
    Facts (retrieved KB)
    Concepts (educational KB)
    User profile (personalization)
        → Generates natural, human-like response.
7. Response generator outputs conversational answer.
8. Utils log conversation for feedback loop.



insurance_chatbot/
│
├── app.py                  # CLI entry point
│
├── core/
│   ├── intent_handler.py    # Classify intents
│   ├── dialogue_manager.py  # Manages conversation flow & profile
│   ├── retrieval.py         # Search KB (policies + concepts)
│   ├── scoring.py           # Profile-to-needs-to-policy scoring engine
│   ├── gpt_handler.py       # LLM interface (retrieval-augmented prompts)
│   └── utils.py             # Helpers (formatting tables, logging, etc.)
│
├── data/
│   ├── policies.json        # Structured policy KB (plan features)
│   └── concepts.json        # Educational KB (co-pay, waiting, exclusions)
│
├── tests/
│   ├── test_intents.py      # Validate intent classification
│   ├── test_retrieval.py    # Validate KB search
│   ├── test_scoring.py      # Validate policy ranking
│   └── golden_conversations.json  # Golden test scenarios
│
├── logs/
│   └── conversations.log    # Store anonymized chat transcripts
│
└── README.md                # Documentation

1. Input Layer

    User interacts via CLI (MVP), extendable later to Streamlit, WhatsApp, web.

    Accepts free-form natural language, not just fixed options.

2. Intent Handling

    Classifies each user input into:

    Greeting

    Profile info (age, dependents, city, chronic, budget)

    Recommendation request

    Policy query (feature-based, e.g., maternity waiting)

    Concept query (educational, e.g., “What is co-pay?”)

    Compare request

    Limitation/exclusion query

    Small talk / fallback

3. Dialogue Manager

    Maintains session state (user profile, history, intent).

    Checks for missing profile info → asks conversationally.

    Decides next step: recommend, explain, compare, or educate.

    Ensures flow feels guided, not rigid (offers micro-choices).

4. Knowledge Layer

    Policy Facts KB (policies.json):

    Each plan variant with structured features (sum insured, maternity, ambulance, OPD, co-pay, room rent, etc.).

    Concept KB (concepts.json):

    Definitions, why it matters, tips (waiting period, co-pay, exclusions, room rent).

    Ensures bot can be both factual and educational.

5. Scoring Engine

    Maps user profile → insurance needs → policy features.

    Uses manual weights (later can evolve to ML).

    Produces ranked list of policies with scores.

6. Retrieval Layer

    Hybrid search (keyword + embeddings) over both KBs.

    Returns:

    Policy features relevant to the user’s question.

    Concept explainers if query is educational.

7. Reasoning & LLM Handler

    Input = (user profile + scored policies + retrieved policy features + concept explainers).

    Prompting ensures:

    Answer is conversational, empathetic, advisor-like.

    Every response includes: Fact → Why it matters → Next step.

    No hallucination → limited to KB context.

8. Response Generator

    Combines:

    Direct factual answer.

    Personalized reasoning (based on profile).

    Educational tip (from concepts.json).

    Presents in natural conversation style.

    Always offers next step (compare, explain further, connect to advisor).

9. Trust & Safety

    Always add disclaimer: “This is informational, not financial advice.”

    Escalate to human agent if: out-of-scope, premium quotes, unclear intent.

    Handle PII carefully (store in session only).

10. Feedback Loop

    Save anonymized conversations for evaluation.

    Golden test set (10–15 scenarios) to validate behavior before release.

    Use transcripts to refine intents, weights, and KB coverage.