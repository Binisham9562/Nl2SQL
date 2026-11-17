import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL")
API_TIMEOUT = int(os.getenv("API_TIMEOUT"))

st.set_page_config(page_title="Khidmah SQL Assistant", page_icon="💬")
st.title("💬 Khidmah SQL Assistant")
st.caption("Ask questions about the database in plain English.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask a question about the data...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(API_URL, json={"question": question}, timeout=API_TIMEOUT)
                response.raise_for_status()
                answer = response.json().get("answer", "No answer returned.")
            except requests.exceptions.RequestException as e:
                answer = f"Request failed: {e}"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

with st.sidebar:
    st.subheader("Settings")
    st.text_input("API URL", value=API_URL, disabled=True, help="Set API_URL in .env")
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()
