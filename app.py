import streamlit as st
from controller.chat_controller import run_chat_controller
import pandas as pd

# ----------------------------
# Session State Initialization
# ----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0

if "total_cost_inr" not in st.session_state:
    st.session_state.total_cost_inr = 0.0

if "user_profile" not in st.session_state:
    st.session_state.user_profile = {}

if "last_bot_action" not in st.session_state:
    st.session_state.last_bot_action = None

if "show_profile_form" not in st.session_state:
    st.session_state.show_profile_form = False

# persistent form defaults
if "form_gender" not in st.session_state:
    st.session_state.form_gender = "Male"
if "form_city_tier" not in st.session_state:
    st.session_state.form_city_tier = "Tier 1"
if "form_members" not in st.session_state:
    st.session_state.form_members = {
        "self": {"checked": True, "age": 35},
        "wife": {"checked": False, "age": 30},
        "mother": {"checked": False, "age": 55},
        "father": {"checked": False, "age": 60},
    }
if "form_children" not in st.session_state:
    st.session_state.form_children = []

# ----------------------------
# Initial Bot Greeting
# ----------------------------
if not st.session_state.chat_history:
    st.session_state.chat_history.append((
        "assistant",
        "How great it is to choose Apollo 24|7 — with our wide hospital network and needs-based insurance designed for everyone. How can we help you today?"
    ))


# ----------------------------
# Sidebar
# ----------------------------
with st.sidebar:
    st.header("Token usage")
    st.write(f"Total tokens: {st.session_state.total_tokens}")
    st.write(f"Estimated cost: ₹{st.session_state.total_cost_inr:.4f}")

    st.subheader("User profile")
    st.json(st.session_state.user_profile)

    st.markdown("---")
    st.subheader("Session Controls")

    # Reset Profile button
    if st.button("🔄 Reset Profile"):
        st.session_state.user_profile = {}
        st.session_state.last_bot_action = "reset_profile"
        st.session_state.show_profile_form = False
        st.session_state.chat_history.append(("assistant", "✅ Profile has been reset. Let's start fresh! What do you want to know about Health Insurance"))

    # End Session button
    if st.button("⏹ End Session"):
        st.session_state.clear()
        st.rerun()

# ----------------------------
# Title
# ----------------------------
st.title("🛡️ Apollo 24|7 Insurance Chatbot")

# ----------------------------
# Display Chat History
# ----------------------------
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)

# ----------------------------
# Chat Input
# ----------------------------
user_input = st.chat_input("Ask me about Health insurance ...")

# ----------------------------
# On new user input, run controller
# ----------------------------
response = None
if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.chat_history.append(("user", user_input))

    response = run_chat_controller(
        user_input=user_input,
        user_profile=st.session_state.user_profile,
        last_bot_action=st.session_state.last_bot_action,
        total_tokens=st.session_state.total_tokens,
        total_cost_inr=st.session_state.total_cost_inr
    )

    # if bot asks for info, flip the flag
    if response.get("updated_last_action") == "ask_info":
        st.session_state.show_profile_form = True
    else:
        with st.chat_message("assistant"):
            st.markdown(response.get("reply", ""))
        st.session_state.chat_history.append(("assistant", response.get("reply", "")))

    # update state from controller
    st.session_state.user_profile = response.get("updated_profile", st.session_state.user_profile)
    st.session_state.last_bot_action = response.get("updated_last_action", st.session_state.last_bot_action)
    st.session_state.total_tokens = response.get("total_tokens", st.session_state.total_tokens)
    st.session_state.total_cost_inr = response.get("total_cost_inr", st.session_state.total_cost_inr)

# ----------------------------
# Always render profile form if flag is set
# ----------------------------
def render_profile_form():
    with st.chat_message("assistant"):
        st.markdown("### Let's get your profile right!")

        # --- Gender ---
        gender = st.radio(
            "Select your gender",
            ["Male", "Female"],
            horizontal=True,
            index=0 if st.session_state.form_gender == "Male" else 1,
            key="gender_radio"
        )
        st.session_state.form_gender = gender

        # --- City tier ---
        city_tier = st.selectbox(
            "Select your city tier",
            ["Tier 1", "Tier 2", "Tier 3"],
            index=["Tier 1", "Tier 2", "Tier 3"].index(st.session_state.form_city_tier),
            key="city_tier_select"
        )
        st.session_state.form_city_tier = city_tier

        # --- Members ---
        st.markdown("Select Members")
        col1, col2 = st.columns(2)

        with col1:
            st.checkbox("Self", value=True, disabled=True, key="self_cb")
            self_age = st.selectbox(
                "Self age", list(range(18, 101)),
                index=st.session_state.form_members["self"]["age"] - 18,
                key="self_age"
            )
            st.session_state.form_members["self"]["checked"] = True
            st.session_state.form_members["self"]["age"] = self_age

            mother_checked = st.checkbox(
                "Mother",
                value=st.session_state.form_members["mother"]["checked"],
                key="mother_cb"
            )
            mother_age = st.selectbox(
                "Mother age", list(range(30, 101)),
                index=st.session_state.form_members["mother"]["age"] - 30,
                key="mother_age"
            )
            st.session_state.form_members["mother"]["checked"] = mother_checked
            st.session_state.form_members["mother"]["age"] = mother_age

        with col2:
            wife_checked = st.checkbox(
                "Wife",
                value=st.session_state.form_members["wife"]["checked"],
                key="wife_cb"
            )
            wife_age = st.selectbox(
                "Wife age", list(range(18, 101)),
                index=st.session_state.form_members["wife"]["age"] - 18,
                key="wife_age"
            )
            st.session_state.form_members["wife"]["checked"] = wife_checked
            st.session_state.form_members["wife"]["age"] = wife_age

            father_checked = st.checkbox(
                "Father",
                value=st.session_state.form_members["father"]["checked"],
                key="father_cb"
            )
            father_age = st.selectbox(
                "Father age", list(range(30, 101)),
                index=st.session_state.form_members["father"]["age"] - 30,
                key="father_age"
            )
            st.session_state.form_members["father"]["checked"] = father_checked
            st.session_state.form_members["father"]["age"] = father_age

        # --- Children ---
        st.markdown("Select children (max 4)")
        add_son_col, add_dau_col = st.columns(2)
        if add_son_col.button("+ Son"):
            if len(st.session_state.form_children) < 4:
                st.session_state.form_children.append({"relation": "son", "age": 3})
        if add_dau_col.button("+ Daughter"):
            if len(st.session_state.form_children) < 4:
                st.session_state.form_children.append({"relation": "daughter", "age": 3})

        for idx, child in enumerate(st.session_state.form_children):
            c1, c2 = st.columns(2)
            with c1:
                rel = st.selectbox(
                    f"Child {idx+1} relation",
                    ["Son", "Daughter"],
                    key=f"child_rel_{idx}",
                    index=0 if child["relation"] == "son" else 1
                )
                st.session_state.form_children[idx]["relation"] = rel.lower()
            with c2:
                age = st.selectbox(
                    f"{rel} age",
                    ["<1"] + list(range(1, 25)),
                    key=f"child_age_{idx}",
                    index=(0 if child["age"] == 0 else child["age"])
                )
                st.session_state.form_children[idx]["age"] = 0 if age == "<1" else int(age)

        # --- Pre-existing conditions ---
        st.markdown("Pre-existing conditions (for any family member)")
        ped_options = [
            "Diabetes",
            "Hypertension (High BP)",
            "Chronic respiratory issues (Asthma/COPD)",
            "Heart or kidney disease",
            "Cancer (past or present)",
            "None of the above"
        ]
        # selected_peds = st.multiselect(
        #     "Select all that apply",
        #     ped_options,
        #     default=["None of the above"] if not st.session_state.get("form_peds") else st.session_state["form_peds"],
        #     key="form_peds"
        # )
        selected_peds = st.multiselect(
            "Select all that apply",
            ped_options,
            default=st.session_state.get("form_peds", []),  # empty by default
            key="form_peds"
        )

        # --- Submit ---
        if st.button("Submit Profile"):
            members = []
            for rel_key, data in st.session_state.form_members.items():
                if data["checked"]:
                    members.append({"relation": rel_key, "age": data["age"]})
            members.extend(st.session_state.form_children)

            profile_update = {
                "gender": st.session_state.form_gender.lower(),
                "location": st.session_state.form_city_tier,
                "members": members,
                "ped_conditions": ([] if "None of the above" in st.session_state.form_peds else [p.lower() for p in st.session_state.form_peds])
            }

            st.session_state.user_profile.update(profile_update)
            st.session_state.last_bot_action = "static"
            st.session_state.show_profile_form = False

            reply = "Thanks, I’ve updated your profile. Would you like me to recommend the best plan, or compare options?"
            members_str = "\n".join([f"  • {m['relation'].capitalize()}: {m['age']} yrs" for m in members])
            summary_text = (
                f"✅ Profile captured:\n"
                f"- Gender: {st.session_state.user_profile['gender']}\n"
                f"- City: {st.session_state.user_profile['location']}\n"
                f"- Members:\n{members_str}\n"
                f"- Pre-existing: {', '.join(st.session_state.user_profile.get('ped_conditions', [])) or 'None'}"
            )
            with st.chat_message("assistant"):
                st.markdown(summary_text)
                st.markdown(reply)

            st.session_state.chat_history.append(("assistant", summary_text))
            st.session_state.chat_history.append(("assistant", reply))


# render profile form if flag is set
if st.session_state.show_profile_form:
    render_profile_form()
