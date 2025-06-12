import streamlit as st
from openai import OpenAI

# Setup page
st.set_page_config(page_title="AI CYOA", page_icon="🧙")
st.title("🧙 Choose Your Own Adventure")
st.write("Start your journey. What do you want to do?")

# Create a text input field
user_input = st.text_input("Your move:", placeholder="Enter something like 'go north' or 'look around'")

# Load OpenAI API key
client = OpenAI(api_key=st.secrets["openai"]["OPENAI_API_KEY"])

# Only call GPT if user types something
if user_input:
    with st.spinner("Thinking..."):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": user_input}],
            temperature=1,
            max_tokens=256
        )
        story = response.choices[0].message.content
        st.markdown(story)

