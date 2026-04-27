import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

from modules.data_loader import load_file
from modules.analyzer import basic_info, describe_data, correlation
from modules.visualizer import show_charts
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
        # 📊 DATA PREVIEW (OLD UI KEPT)
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

        # =========================
        # 🔥 CORRELATION (FIXED + GRAPH ADDED)
        # =========================
        st.subheader("Correlation")

        corr = correlation(df)

        # table (old behavior)
        st.write(corr)

        # heatmap (new feature added)
        try:
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.heatmap(
                corr,
                annot=True,
                cmap="coolwarm",
                fmt=".2f",
                linewidths=0.5,
                ax=ax
            )
            st.pyplot(fig)
        except:
            st.warning("Install seaborn for heatmap: pip install seaborn")

        # =========================
        # 📊 CHARTS (OLD + NEW)
        # =========================
        show_charts(df)

        # Extra simple chart (NEW)
        st.subheader("Quick Visualization")

        numeric_cols = df.select_dtypes(include="number").columns

        if len(numeric_cols) > 0:
            col = st.selectbox("Select column", numeric_cols)

            fig, ax = plt.subplots()
            ax.hist(df[col], bins=20)
            st.pyplot(fig)

        # =========================
        # 🤖 AI INSIGHTS (FIXED BULLETS)
        # =========================
        st.subheader("AI Generated Insights")

        mode = st.selectbox("Select Mode", ["normal", "beginner", "business"])

        if st.button("Generate Insights"):
            insights = generate_insights(df, mode)

            for line in insights.split("\n"):
                st.write(line)

        # =========================
        # 💬 Q&A (IMPROVED BUT SAME UI)
        # =========================
        st.subheader("Ask Questions About Data")

        col1, col2 = st.columns([4, 1])

        with col1:
            question = st.text_input("Enter your question")

        with col2:
            ask_btn = st.button("Ask")

        if ask_btn and question:
            answer = ask_question(df, question)

            add_to_memory(question, answer)

            st.subheader("Answer")
            st.write(answer)

        # Clear button (fixed)
        if st.button("Clear Chat"):
            st.session_state.memory = []
            st.experimental_rerun()

        # =========================
        # 🧠 CHAT HISTORY (OLD UI)
        # =========================
        st.subheader("Chat History")
        display_memory()

    else:
        st.error("Error loading file")