import faiss
import json
import numpy as np
import os
from core.gpt_handler import call_gpt
from openai import OpenAI
import streamlit as st


# -------------------------
# Load Knowledge Sources
# -------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
index = faiss.read_index(os.path.join(DATA_DIR, "kb.index"))

with open(os.path.join(DATA_DIR, "kb.json"), "r") as f:
    metadata = json.load(f)

with open(os.path.join(DATA_DIR, "knowledge_base_merged.json"), "r") as f:
    kb_struct = json.load(f)


# -------------------------
# OpenAI Client Initialization
# -------------------------
def get_openai_client():
    """Get OpenAI client with API key from Streamlit secrets."""
    api_key = st.secrets["openai"]["api_key"]
    return OpenAI(api_key=api_key)


# -------------------------
# FAISS-based Retrieval
# -------------------------
def embed_text(text, model="text-embedding-3-small"):
    """Embed text using OpenAI's embedding model."""
    client = get_openai_client()
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding


def search_index(query_embedding, top_k=3):
    """Search FAISS index and return top_k chunks from kb.json."""
    D, I = index.search(np.array([query_embedding]).astype("float32"), top_k)
    results = []
    for score, idx in zip(D[0], I[0]):
        if idx < 0:
            continue
        entry = metadata[idx]
        results.append({
            "text": entry.get("content", ""),
            "policy": entry.get("policy", ""),
            "insurer": entry.get("insurer", ""),
            "variant": entry.get("variant", ""),
            "section": entry.get("section", ""),
            "tags": entry.get("feature_tags", []),
            "score": float(score)
        })
    return results


# -------------------------
# Structured KB Helpers
# -------------------------
def list_all_policies():
    return [
        {"policy": p["name"], "insurer": p["insurer"]}
        for p in kb_struct["policies"]
    ]


def list_all_insurers():
    return sorted(set(p["insurer"] for p in kb_struct["policies"]))


def best_policy_for_maternity():
    results = []
    for p in kb_struct["policies"]:
        for v in p["variants"]:
            wp = v.get("waiting_periods", {}).get("maternity", "")
            if wp:
                results.append({
                    "policy": p["name"],
                    "insurer": p["insurer"],
                    "variant": v["variant_name"],
                    "waiting_period": wp
                })
    return results


def get_policies_by_insurer(insurer_name):
    """Find all policies from a specific insurer."""
    insurer_lower = insurer_name.lower()
    results = []
    
    for p in kb_struct["policies"]:
        if insurer_lower in p["insurer"].lower():
            results.append({
                "policy": p["name"],
                "insurer": p["insurer"],
                "uin": p.get("uin", ""),
                "variants": [v["variant_name"] for v in p["variants"]]
            })
    
    return results


# -------------------------
# Hybrid Retrieval (Main Function)
# -------------------------
def retrieve_answer(query, top_k=5, summarize=True, conversational=True):
    """
    Route query to structured KB or FAISS depending on type.
    Returns a conversational response with follow-up questions.
    """
    q = query.lower()

    # --- Structured KB Queries ---
    # General policy listing (expanded pattern matching)
    policy_list_keywords = [
        ("polic", "have"), ("polic", "list"), ("polic", "offer"),
        ("polic", "available"), ("polic", "provide"), ("polic", "sell"),
        ("what polic", ""), ("show polic", ""), ("tell polic", ""),
        ("all polic", ""), ("your polic", "")
    ]
    
    should_list_all = False
    for kw1, kw2 in policy_list_keywords:
        if kw2:
            if kw1 in q and kw2 in q:
                should_list_all = True
                break
        else:
            if kw1 in q:
                should_list_all = True
                break
    
    if should_list_all:
        # Make sure it's not asking about a specific insurer
        insurer_in_query = any(ins in q for ins in ["hdfc", "icici", "star", "niva", "care"])
        
        if not insurer_in_query:
            policies = list_all_policies()
            output = "We offer the following health insurance policies:\n\n"
            for p in policies:
                output += f"• **{p['policy']}** by {p['insurer']}\n"
            if conversational:
                output += "\n💡 Would you like to know more about any specific policy, or shall I recommend the best one for you?"
            return {
                "output": output,
                "tokens_used": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
                "cost_inr": 0.0
            }

    # Check if asking about specific insurer's policies (improved matching)
    insurer_keywords = {
        "hdfc": ["hdfc"],
        "icici": ["icici"],
        "star": ["star health", "star"],
        "niva": ["niva bupa", "niva"],
        "care": ["care health", "care"]
    }
    
    for insurer_key, variations in insurer_keywords.items():
        # Check if any variation of the insurer name is in the query
        insurer_found = any(var in q for var in variations)
        # Check if query is about policies/plans
        policy_mentioned = any(word in q for word in ["polic", "plan", "product", "scheme"])
        
        if insurer_found and policy_mentioned:
            # Get the primary keyword for lookup
            lookup_keyword = variations[0].split()[0]  # Get first word (hdfc, icici, etc)
            policies = get_policies_by_insurer(lookup_keyword)
            
            if policies:
                output = f"Here are the policies from **{policies[0]['insurer']}**:\n\n"
                for p in policies:
                    output += f"• **{p['policy']}** (Variants: {', '.join(p['variants'])})\n"
                if conversational:
                    output += f"\n💡 Would you like to know more about any of these plans or compare them?"
            else:
                output = f"I couldn't find any policies from {variations[0].title()} in our current offerings. We work with HDFC Ergo, ICICI Lombard, Star Health, Niva Bupa, and Care Health Insurance."
                if conversational:
                    output += "\n\n💡 Would you like to see all available policies or get a recommendation?"
            
            return {
                "output": output,
                "tokens_used": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
                "cost_inr": 0.0
            }
    
    # General insurer list query
    if "company" in q or "insurer" in q:
        insurers = list_all_insurers()
        output = "We partner with these trusted insurers:\n\n" + "\n".join([f"• {ins}" for ins in insurers])
        if conversational:
            output += "\n\n💡 Do you have a preference, or would you like me to recommend the best plan based on your needs?"
        return {
            "output": output,
            "tokens_used": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "cost_inr": 0.0
        }

    if "best" in q and "maternity" in q:
        mat_policies = best_policy_for_maternity()
        output = "Here are plans with maternity coverage:\n\n"
        for p in mat_policies[:3]:
            output += f"• **{p['policy']}** ({p['variant']}) - Waiting period: {p['waiting_period']}\n"
        if conversational:
            output += "\n💡 Would you like to know premium details or compare these plans?"
        return {
            "output": output,
            "tokens_used": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "cost_inr": 0.0
        }

    # --- FAISS Q&A with RAG ---
    query_emb = embed_text(query)
    docs = search_index(query_emb, top_k=top_k)

    if not docs:
        return {
            "output": "I couldn't find specific information about that. Could you rephrase your question, or would you like me to recommend a plan for you?",
            "tokens_used": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "cost_inr": 0.0
        }

    context = "\n\n".join([f"[{d['policy']} - {d['variant']}]\n{d['text']}" for d in docs])

    if not summarize:
        return {
            "output": context,
            "tokens_used": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "cost_inr": 0.0
        }

    # Build conversational prompt for RAG
    system_content = """You are a helpful insurance assistant for Apollo 24|7.

Guidelines:
- Use ONLY the provided context to answer (do not make up information)
- For WAITING PERIOD questions, provide ALL types: Initial (30 days), Specific Diseases (24 months), PED/Pre-existing (36-48 months), and Maternity if applicable
- Always mention the exact policy and variant names (e.g., "Aspire - Gold+" by Niva Bupa, "Elevate" by ICICI Lombard)
- Include specific numbers and timeframes (don't say "waiting period applies", say "36 months")
- Keep responses in 4-6 bullet points for completeness
- Be conversational and friendly
- Always end with a helpful follow-up question
- Suggest next steps like: "Would you like to compare these plans?", "Should I recommend the best plan for you?", "Want to see premium estimates?"

IMPORTANT: When answering about insurers/companies, mention the ACTUAL insurer name from context (HDFC Ergo, ICICI Lombard, Star Health, Niva Bupa, Care Health Insurance).
"""

    user_content = f"""Context from our knowledge base:

{context}

User Question: {query}

Provide a clear, concise answer and end with an engaging follow-up question."""

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]

    return call_gpt(messages, model="gpt-4o-mini", temperature=0)
