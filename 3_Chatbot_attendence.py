# Lab 3: Chatbot page - on-theme ACC football attendance assistant (no tools, no outside data)

import time

import streamlit as st
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider


DEBUG = False 

MODELS = ["gemini-3.8-flash", "gemini-3.5-flash-lite"] #we had trouble with our ai model for our chatbox so we had to put a backup 
TRIES_PER_MODEL = 2
WAIT_SECONDS = 4

st.title("Attendance Chatbot")
st.write("Ask the chatbotabout ACC football game days and how athletic departments plan for crowds.")

INSTRUCTIONS = """
You are GameDay Helper, a friendly assistant for college athletic department staff who plan
ACC football game days. Talk about what drives attendance (opponent, rivalry games, weather,
day and time of the game, team success, ticket pricing, student turnout) and how staff can
plan staffing, concessions, parking, and seating. Keep answers short (2-5 sentences).
You do not have access to any real data. If asked for an exact attendance number, stadium
capacity, or score, say you can't look that up here and point the user to the Attendance
page. Politely steer off topic questions back to football attendance and game planning.
"""


@st.cache_resource #prevent reubuilding with every message
def get_agent(model_name):
    """Create an agent for one model, using the Gemini key from Streamlit secrets."""
    provider = GoogleProvider(api_key=st.secrets["GOOGLE_API_KEY"])
    model = GoogleModel(model_name, provider=provider)
    return Agent(model, instructions=INSTRUCTIONS)


# Memory: messages for display, history for the agent
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

prompt = st.chat_input("Ask about game day planning.")

if prompt:
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        reply = None
        last_error = None
        with st.spinner("Please wait while I think!"):
            for model_name in MODELS:
                for attempt in range(TRIES_PER_MODEL):
                    try:
                        result = get_agent(model_name).run_sync(
                            prompt, message_history=st.session_state.chat_history
                        )
                        reply = result.output
                        st.session_state.chat_history = result.all_messages()
                        break
                    except Exception as error:
                        last_error = error
                        time.sleep(WAIT_SECONDS)  # wait, then try again
                if reply is not None:
                    break

        if reply is None:
            if DEBUG:
                reply = f"Sorry, something went wrong. ({last_error})"
            else:
                reply = "Sorry, something went wrong. Please try again later."
        st.write(reply)

    st.session_state.chat_messages.append({"role": "assistant", "content": reply})