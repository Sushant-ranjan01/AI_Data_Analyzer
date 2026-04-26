import streamlit as st

def init_memory():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

def add_to_memory(question, answer):
    st.session_state.chat_history.append((question, answer))

def display_memory():
    for q, a in st.session_state.chat_history:
        st.write("Question:", q)
        st.write("Answer:", a)