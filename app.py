import streamlit as st
from modules.data_loader import load_file
from modules.analyzer import basic_info, describe_data, correlation
from modules.visualizer import show_charts, show_correlation
from modules.ai_engine import generate_insights, ask_question
from modules.chat_memory import init_memory, add_to_memory, display_memory

st.set_page_config(page_title="GenAI Data Analyst", layout="wide")

st.title("GenAI Smart Data Analyst")

init_memory()

uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

if uploaded_file:
    df = load_file(uploaded_file)

    if df is not None:

        # =========================
        # 📊 DATA SECTION
        # =========================
        st.subheader("Data Preview")
        st.write(df.head())

        info = basic_info(df)

        st.subheader("Basic Information")
        st.write("Shape:", info["shape"])
        st.write("Columns:", info["columns"])
        st.write("Missing Values:")
        st.write(info["missing"])

        st.subheader("Statistical Description")
        st.write(describe_data(df))

        corr = correlation(df)
        show_correlation(corr)
        show_charts(df)

        # =========================
        # 🤖 AI INSIGHTS
        # =========================
        st.subheader("AI Generated Insights")

        mode = st.selectbox("Select Mode", ["normal", "beginner", "business"])

        if "insights" not in st.session_state:
            st.session_state.insights = ""

        if st.button("Generate Insights"):
            with st.spinner("Generating insights..."):
                st.session_state.insights = generate_insights(df, mode)

        if st.session_state.insights:
            st.markdown("### Key Insights")
            st.markdown(st.session_state.insights)

        # =========================
    # 💬 Q&A SECTION
    # =========================
    st.subheader("Ask Questions About Data")

    if "last_question" not in st.session_state:
        st.session_state.last_question = ""

    if "current_answer" not in st.session_state:
        st.session_state.current_answer = ""

    # 👉 Better alignment
    col1, col2 = st.columns([5,1])   # increase space for input

    with col1:
        question = st.text_input("Enter your question", key="question")

    with col2:
        st.write("")  # spacing
        st.write("")  # push button down
        ask_btn = st.button("Ask", use_container_width=True)

    # Ask logic
    if ask_btn:
        if question and question != st.session_state.last_question:
            answer = ask_question(df, question)

            add_to_memory(question, answer)

            st.session_state.last_question = question
            st.session_state.current_answer = answer

    # Show answer
    if st.session_state.current_answer:
        st.subheader("Answer")
        st.success(st.session_state.current_answer)

    # Clear chat
    if st.button("Clear Chat"):
        st.session_state.memory = []
        st.session_state.last_question = ""
        st.session_state.current_answer = ""
        st.rerun()