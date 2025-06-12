import re
import streamlit as st
from openai import OpenAI

# -----------------------------------------------------------------------------
# AI‑powered Choose‑Your‑Own‑Adventure – Streamlit front‑end
# -----------------------------------------------------------------------------
# 2025‑06‑12 – iteration 4
# * **Robust choice detection** – we now pick up lines like `1) text`, `1. text`,
#   or `1 ‑ text` using a regex instead of a strict startswith check.
# * If the AI forgets to supply choices, we show a gentle warning plus the
#   free‑form input so the player is never stuck.
# -----------------------------------------------------------------------------

# -----------------------------  Page setup  -----------------------------------
st.set_page_config(page_title="AI CYOA", page_icon="🧙", layout="wide")
st.title("🧙 Choose Your Own Adventure")

# ------------------------  Session‑state helpers  -----------------------------
SYSTEM_PROMPT = (
    "You are a retro 1980s text‑adventure game engine. "
    "Describe scenes vividly in Markdown (using **bold** for emphasis and lists for inventories). "
    "**Always** finish with 3‑5 numbered choices using the format `1. Your text`. "
    "Use the conversation so far as canonical game state."
)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]


# ----------------------------  Sidebar UI  ------------------------------------

def new_game():
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    st.session_state.last_choice = None
    st.rerun()

st.sidebar.header("Game Controls")
st.sidebar.button("🔄 New game / reset", on_click=new_game)
last = st.session_state.get("last_choice")
if last:
    st.sidebar.markdown(f"**Last action:** {last}")

# ---------------------------  OpenAI wrapper  ---------------------------------

def call_ai(user_move: str) -> str:
    client = OpenAI(api_key=st.secrets["openai"]["OPENAI_API_KEY"])
    st.session_state.messages.append({"role": "user", "content": user_move})
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=st.session_state.messages,
        temperature=1.0,
        max_tokens=256,
    )
    reply = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": reply})
    return reply


# ---------------------------  Render history  ---------------------------------
for m in st.session_state.messages[1:]:
    if m["role"] == "assistant":
        st.markdown(m["content"])
    else:
        st.markdown(f"**You:** {m['content']}")

# --------------------------  Current state ------------------------------------
user_has_moved = any(m["role"] == "user" for m in st.session_state.messages)


# ----------------------  First turn UI  --------------------------------------
if not user_has_moved:
    st.markdown("### What do you want to do?")
    col1, col2 = st.columns(2)

    def _first(move: str):
        st.session_state.last_choice = move
        call_ai(move)
        st.rerun()

    with col1:
        if st.button("🌲 Explore the forest"):
            _first("Explore the forest")
    with col2:
        if st.button("🏰 Approach the castle"):
            _first("Approach the castle")

# -----------------------  Later turns UI  ------------------------------------
else:
    # Find the most recent assistant message
    last_ai = next((m["content"] for m in reversed(st.session_state.messages)
                    if m["role"] == "assistant"), "")

    # Regex matches lines like "1. text", "1) text", "1 ‑ text"
    choice_pattern = re.compile(r"^\s*(\d+)[\.)\-]\s+(.*)$")
    numbered = []
    for ln in last_ai.splitlines():
        m = choice_pattern.match(ln)
        if m:
            numbered.append(m.group(2).strip())

    if numbered:
        st.markdown("#### Choose an option:")
        for label in numbered:
            if st.button(label):
                st.session_state.last_choice = label
                call_ai(label)
                st.rerun()
    else:
        st.info(
            "The game engine forgot to give numbered options. "
            "You can still type a command below (e.g. `look around`)."
        )

    st.markdown("---")

    user_move = st.text_input(
        "Or type your command:",
        placeholder="e.g. go north, look around, inventory",
        key="freeform_input",
    )
    if user_move:
        st.session_state.last_choice = user_move
        call_ai(user_move)
        st.session_state.freeform_input = ""
        st.rerun()
