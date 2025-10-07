from core.dialogue_manager import handle_dialogue
from core.intent_handler import classify_intent
from core.gpt_handler import call_gpt
from core.retrieval import retrieve_answer
from core.premium_api import get_premium_quotes_conversational, fetch_premium_quotes
from core.matrix_recommendation import get_matrix_recommendations
from core.sequential_profiler import (
    get_next_profile_question,
    parse_yes_no_response,
    should_ask_more_questions,
    get_profile_completion_status
)
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

def run_chat_controller(user_input, user_profile, last_bot_action, total_tokens, total_cost_inr, hop_count=0):
    # Step 1: Use existing user_profile (no GPT extraction now)
    updated_profile = dict(user_profile)

    # Step 2: Classify intent (string output, not dict)
    intent_result = classify_intent(user_input)
    intent = intent_result["output"]
    
    # Step 2.5: Handle sequential profiling (NEW!)
    # If last action was asking a sequential question, capture the response
    if last_bot_action and last_bot_action.startswith("asking_"):
        question_key = last_bot_action.replace("asking_", "")
        response = parse_yes_no_response(user_input)
        
        if response is not None:  # Valid yes/no response
            updated_profile[question_key] = response
            
            # Check if we should ask another question or proceed
            next_question = get_next_profile_question(updated_profile)
            
            if next_question and intent not in ["recommend", "compare", "premium_quote", "goodbye"]:
                # Ask next question in sequence
                q_key, q_text, q_explanation = next_question
                reply = q_text
                
                return {
                    "reply": reply,
                    "action": "ask_sequential",
                    "updated_profile": updated_profile,
                    "updated_last_action": f"asking_{q_key}",
                    "total_tokens": total_tokens,
                    "total_cost_inr": total_cost_inr,
                    "flow_suggest": []
                }
            else:
                # Done with questions OR user explicitly requested an action
                # Provide acknowledgment and proceed
                status = get_profile_completion_status(updated_profile)
                completion_msg = f"✅ Got it! (Profile: {status['completion_percentage']}% complete)\n\n"
                
                # If user didn't explicitly request an action, ask what they want to do
                if intent not in ["recommend", "compare", "premium_quote"]:
                    reply = completion_msg + "Now, would you like me to:\n• Recommend the best plans for you?\n• Compare specific policies?\n• Get premium quotes?"
                    return {
                        "reply": reply,
                        "action": "profile_complete",
                        "updated_profile": updated_profile,
                        "updated_last_action": "profile_complete",
                        "total_tokens": total_tokens,
                        "total_cost_inr": total_cost_inr,
                        "flow_suggest": ["recommend", "compare", "premium_quote"]
                    }
                # Otherwise, fall through to handle their explicit request
    
    # Step 3: Dialogue manager
    result = handle_dialogue(
        user_input=user_input,
        user_profile=updated_profile,
        intent=intent,
        last_bot_action=last_bot_action,
        hop_count=hop_count
    )

    print('----------------------')
    print(user_input)
    print(intent)
    print(result)
    print('----------------------')
    
    # Step 3.5: SAFETY CHECK - Don't ask for profile on catalog queries
    # If GPT misclassified a catalog query, catch it here
    if result["action"] == "ask_info":
        # Check if user is asking about policies/plans/insurers (catalog browsing)
        # Use GPT to determine if this is really a catalog query
        user_lower = user_input.lower()
        catalog_indicators = ['polic', 'plan', 'insurer', 'company', 'hdfc', 'icici', 
                             'star', 'niva', 'care', 'offer', 'have', 'available']
        
        if any(indicator in user_lower for indicator in catalog_indicators):
            # Possible catalog query - verify with GPT
            verify_prompt = f"""User query: "{user_input}"

Is this user asking to BROWSE available insurance policies/plans/insurers (general catalog query)?
OR are they asking for PERSONALIZED recommendations specifically for them?

Answer ONLY "catalog" or "personalized"."""
            
            verify_response = call_gpt(
                [{"role": "user", "content": verify_prompt}],
                model="gpt-4o-mini",
                temperature=0
            )
            
            total_tokens += verify_response.get("tokens_used", 0)
            total_cost_inr += verify_response.get("cost_inr", 0)
            
            verification = verify_response.get("output", "").strip().lower()
            
            if "catalog" in verification:
                # Override: This is a catalog query, not profile collection
                # Route to RAG retrieval
                retrieval_response = retrieve_answer(
                    query=user_input,
                    top_k=5,
                    summarize=True,
                    conversational=True
                )
                reply = retrieval_response["output"]
                total_tokens += retrieval_response["tokens_used"]
                total_cost_inr += retrieval_response["cost_inr"]
                
                return {
                    "reply": reply,
                    "action": "catalog_info",
                    "updated_profile": updated_profile,
                    "updated_last_action": "catalog_info",
                    "total_tokens": total_tokens,
                    "total_cost_inr": total_cost_inr,
                    "flow_suggest": []
                }
    
    # Step 4: Generate reply
    if result["action"] == "ask_info":
        miss = missing_fields(result["updated_profile"])

        if not miss:
            # Edge case: nothing missing but still got ask_info
            reply = "Thanks, I have all the details I need. Let’s move ahead with recommendations."
            return {
                "reply": reply,
                "action": "recommend",
                "updated_profile": result["updated_profile"],
                "updated_last_action": "recommend",
                "total_tokens": total_tokens,
                "total_cost_inr": total_cost_inr,
                "flow_suggest": result.get("flow_suggest", [])
            }

        # Normal ask_info flow → GPT generates a question for one missing field
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
        # Check if we should ask more profile questions first
        if should_ask_more_questions(updated_profile, "recommend"):
            next_question = get_next_profile_question(updated_profile)
            if next_question:
                q_key, q_text, q_explanation = next_question
                reply = "To give you the best recommendations, let me ask a few quick questions!\n\n" + q_text
                return {
                    "reply": reply,
                    "action": "ask_sequential",
                    "updated_profile": updated_profile,
                    "updated_last_action": f"asking_{q_key}",
                    "total_tokens": total_tokens,
                    "total_cost_inr": total_cost_inr,
                    "flow_suggest": []
                }
        
        # Use new matrix-based recommendation engine
        recom_resp = get_matrix_recommendations(updated_profile, top_n=3)

        # --- prepare score data from matrix engine ---
        top_policies = recom_resp.get("top_policies", [])
        top3 = [(p["policy"], p["score"]) for p in top_policies[:3]]
        
        # --- get user needs from matrix engine ---
        user_needs = [need["need"].replace("_", " ").title() for need in recom_resp.get("top_needs", [])[:8]]
        user_needs_list = ", ".join(user_needs[:5])  # Top 5 for display

        # --- build system prompt with explanations ---
        top_policies = recom_resp.get("top_policies", [])
        
        # Build feature-rich comparison for each policy
        policy_details = []
        for i, p in enumerate(top_policies[:3]):
            rank_display = ["🥇 1st Choice", "🥈 2nd Choice", "🥉 3rd Choice"][i]
            why_features = [n['need'].replace('_', ' ').title() for n in p.get('why_recommended', [])[:5]]  # Show top 5 features
            policy_details.append({
                "rank": rank_display,
                "name": p['policy'],
                "score_backend": p['score'],  # Keep for backend
                "features": why_features
            })
        
        # Create detailed explanations with ranks (not scores)
        explanations = "\n".join([
            f"{pd['rank']}: {pd['name']}\n   Key Features for User: {', '.join(pd['features'])}"
            for pd in policy_details
        ])
        
        # Check if Apollo plans are in top 3 (for advantage messaging)
        has_apollo = any("Apollo" in p['policy'] or "Optima" in p['policy'] for p in top_policies[:3])
        apollo_advantage = """
        
        💡 **Apollo Advantage:** Apollo plans benefit from being both the insurer AND having their own hospital network (14,000+ Apollo hospitals). This means:
        • Faster cashless approvals
        • Better coordination between hospitals and insurance
        • Dedicated Apollo support
        • Pre-verified network quality
        """ if has_apollo else ""
        
        system_prompt = textwrap.dedent(f"""
            You are a friendly and knowledgeable insurance advisor for Apollo 24|7. Based on the data below, create a warm, conversational recommendation:
            
            1. Start with: "Based on your profile, I've analyzed what matters most to you: **{user_needs_list}**. Here are my recommendations:"
            
            2. Recommend the **#1 choice** with enthusiasm (~120-150 words):
               - Explain why this plan is perfect for them
               - Highlight 4-5 specific features that match their needs
               - Mention Sum Insured (5L-10L for young, 10L-25L for families, 25L+ for seniors)
               - Suggest policy term (1 year for trial, 2-3 years for savings)
            
            3. Briefly mention the **2nd and 3rd choices** (1-2 sentences each)
               - Explain what makes each unique
            
            4. Create a DETAILED comparison table (Markdown) for top 3 plans:
               | Plan | Ranking | Key Benefits for Your Profile | Network | Special Features |
               
               For "Key Benefits" column, list 4-5 specific features from their profile needs: {user_needs_list}
               Use checkmarks for each: ✅ Feature
               
               Example row:
               | Super Star | 🥇 1st | ✅ Telemedicine, ✅ Air Ambulance, ✅ Home Care, ✅ Wellness Benefits, ✅ No Copay | 14,000+ hospitals | Unlimited automatic restoration |
               
               Make it detailed and feature-rich to show WHY these plans match their needs perfectly.
            {apollo_advantage}
            
            5. End with a helpful conversational close:
               "💬 Want to explore more? I can:
               • Show you premium estimates for any of these plans
               • Explain specific features in detail (like PED coverage, room rent, etc.)
               • Compare these plans side-by-side
               
               What would you like to know?"

            Data for your recommendation:
            {explanations}
            
            User profile: {updated_profile}
            Top needs identified: {user_needs_list}
            
            IMPORTANT: 
            - Show RANKINGS (🥇 1st, 🥈 2nd, 🥉 3rd), NOT scores/ratings
            - Make comparison table FEATURE-RICH with specifics
            - Connect features to user's needs explicitly
            - Make it believable by showing WHY each feature matters for them
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
        # Check if we should ask more profile questions first
        if should_ask_more_questions(updated_profile, "compare"):
            next_question = get_next_profile_question(updated_profile)
            if next_question:
                q_key, q_text, q_explanation = next_question
                reply = "To give you the best comparison, let me ask a few quick questions!\n\n" + q_text
                return {
                    "reply": reply,
                    "action": "ask_sequential",
                    "updated_profile": updated_profile,
                    "updated_last_action": f"asking_{q_key}",
                    "total_tokens": total_tokens,
                    "total_cost_inr": total_cost_inr,
                    "flow_suggest": []
                }
        
        # Use new matrix-based recommendation engine
        recom_resp = get_matrix_recommendations(updated_profile, top_n=3)

        # --- prepare score data from matrix engine ---
        top_policies = recom_resp.get("top_policies", [])
        
        # --- get user needs from matrix engine ---
        user_needs = [need["need"].replace("_", " ").title() for need in recom_resp.get("top_needs", [])[:8]]
        user_needs_list = ", ".join(user_needs[:5])  # Top 5 for display
        
        # Build policy details with rankings
        policy_details = []
        for i, p in enumerate(top_policies[:3]):
            rank_display = ["🥇 1st", "🥈 2nd", "🥉 3rd"][i]
            why_features = [n['need'].replace('_', ' ').title() for n in p.get('why_recommended', [])[:4]]
            policy_details.append({
                "rank": rank_display,
                "name": p['policy'],
                "features": why_features
            })
        
        # Check if Apollo plans are in top 3
        has_apollo = any("Apollo" in p['policy'] or "Optima" in p['policy'] for p in top_policies[:3])
        apollo_advantage = """
        
        💡 **Apollo Advantage:** Apollo plans combine insurer + hospital network (14,000+ Apollo hospitals):
        • Faster cashless approvals (within 2 hours)
        • Better hospital-insurance coordination
        • Dedicated support & pre-verified quality
        """ if has_apollo else ""

        # --- build system prompt for comparison ---
        system_prompt = textwrap.dedent(f"""
            You are a friendly insurance advisor helping users make informed decisions. Create a helpful comparison of plans:

            1. Start with: "Based on your profile, I've identified what matters most to you: **{user_needs_list}**. Here's how the top plans compare:"
            
            2. Create a DETAILED Markdown comparison table with 5 columns:
               | Plan Name | Ranking | Key Benefits Matching Your Needs | Hospital Network | Unique Features |
               
               For "Key Benefits" column, explicitly list 3-4 features from user's needs: {user_needs_list}
               Use checkmarks: ✅ Feature Name
               
               Example row:
               | Super Star | 🥇 1st | ✅ Telemedicine, ✅ Air Ambulance, ✅ Home Care, ✅ Wellness Benefits | 14,000+ (Star Health) | Unlimited automatic restoration |
               
               Make it feature-rich and specific to show HOW each plan meets their needs.
            {apollo_advantage}
            
            3. After the table, provide 4-5 clear insights:
               - **Coverage Match:** Which plan best matches their top needs ({user_needs_list})
               - **Unique Strengths:** What makes each plan special
               - **Waiting Periods:** Important timelines to know
               - **Best For:** Recommend which plan for which scenario
            
            4. End with: "Which plan would you like to explore further? I can show premium quotes or explain any features in detail!"

            Comparison data:
            Policy rankings: {[pd['rank'] + ': ' + pd['name'] for pd in policy_details]}
            User profile: {updated_profile}
            Top needs: {user_needs_list}
            
            IMPORTANT:
            - Show RANKINGS (🥇 1st, 🥈 2nd, 🥉 3rd), NOT scores
            - Make table FEATURE-RICH with specifics
            - Connect features to user's identified needs
            - Make it believable by showing WHY features matter
        """)

        # --- GPT call ---
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User intent: compare. Question: {user_input}"}
        ]
        gpt_response = call_gpt(messages)

        reply = gpt_response["output"]
        total_tokens += gpt_response["tokens_used"]
        total_cost_inr += gpt_response["cost_inr"]

    elif result["action"] == "premium_quote":
        # Check if profile is complete
        miss = missing_fields(updated_profile)
        
        if miss:
            reply = "To get accurate premium quotes, I need a bit more information about you. Let me ask you a few quick questions!"
            return {
                "reply": reply,
                "action": "ask_info",
                "updated_profile": result["updated_profile"],
                "updated_last_action": "ask_info",
                "total_tokens": total_tokens,
                "total_cost_inr": total_cost_inr,
                "flow_suggest": result.get("flow_suggest", [])
            }
        
        # Fetch real-time premium quotes
        try:
            # Try to get auth token from Streamlit secrets (optional)
            import streamlit as st
            auth_token = st.secrets.get("apollo_api", {}).get("auth_token", None)
        except:
            auth_token = None
        
        # Get premium quotes
        reply = get_premium_quotes_conversational(updated_profile, auth_token)
        
        # No GPT tokens used for API call
        # (tokens already tracked if any)
        
    elif result["action"] == "static":
        reply = result["response"]

    elif result["action"] == "call_gpt":
        # Check if this is a knowledge query that should use RAG
        knowledge_intents = [
            "policy_query", "rider_query", "limitation_query", "eligibility_query",
            "claims_query", "network_query", "concept_query", "catalog_info",
            "process_query", "renewal_query", "cancellation_query"
        ]
        
        if intent in knowledge_intents:
            # Use RAG retrieval for knowledge-based queries
            retrieval_response = retrieve_answer(
                query=user_input,
                top_k=5,  # Increased from 3 to 5 for more comprehensive answers
                summarize=True,
                conversational=True
            )
            reply = retrieval_response["output"]
            total_tokens += retrieval_response["tokens_used"]
            total_cost_inr += retrieval_response["cost_inr"]
        else:
            # For general queries, use GPT with custom prompt
            system_prompt = """
            You are a helpful health insurance advisor for Apollo 24|7 users.
            Your goal is to provide accurate, friendly, and fact-based information about **Health Insurance only**.

            Guidelines:
            - Talk only about Health Insurance (ignore auto, life, motor, or travel insurance).
            - Keep responses in concise bullet points (max 5).
            - Always end with a short, conversational follow-up question to keep users engaged.
            - If the query is about *types of health insurance*, explain only two:
              1. Retail Health Insurance – individual or family policies bought personally.
              2. Group Health Insurance – employer or organization-provided coverage.
            - Always encourage users to explore plans, compare options, or get personalized recommendations.
            """
            # Use the contextual instruction from handle_dialogue() if available
            context_msg = result.get("response") or f"User intent: {intent}. Question: {user_input}"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context_msg}
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
        "total_cost_inr": total_cost_inr,
        "flow_suggest": result.get("flow_suggest", [])  # expose suggestions to UI
    }