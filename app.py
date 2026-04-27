import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile
import os

def ask_question(df, question):

    q = question.lower()

    # normalize words
    q = q.replace("_", " ")
    q = q.replace("hours", "hour")
    q = q.replace("hrs", "hour")

    numeric_cols = df.select_dtypes(include='number').columns
    all_cols = df.columns

    # create searchable column map
    col_map = {
        col: col.lower().replace("_", " ")
        for col in all_cols
    }

    best_match = None
    best_score = 0

    # 🔥 UNIVERSAL MATCHING (FIXED)
    for col, clean in col_map.items():

        words = clean.split()

        score = sum(1 for w in words if w in q)

        # substring boost
        if clean in q:
            score += 2

        if score > best_score:
            best_score = score
            best_match = col

    # 🔥 extra smart responses
    if "summary" in q or "dataset" in q:
        return f"This dataset contains {df.shape[0]} rows and {df.shape[1]} columns."

    if "columns" in q:
        return f"Columns are: {', '.join(df.columns)}"

    # =========================
    # 🎯 CORRELATION (MOVED UP)
    # =========================
    if "correlation" in q or "relationship" in q:
        if len(numeric_cols) > 1:
            corr = df[numeric_cols].corr().abs()

            for i in range(len(corr)):
                corr.iloc[i, i] = 0

            pair = corr.unstack().idxmax()
            val = corr.unstack().max()

            return f"The strongest relationship is between {pair[0]} and {pair[1]} (correlation {val:.2f})"

    # ❌ no match
    if best_score == 0:
        return "Couldn't find a relevant column. Try using column-related words."

    # =========================
    # 🎯 NUMERIC OPERATIONS
    # =========================
    if best_match in numeric_cols:

        if "average" in q or "mean" in q:
            return f"The average {best_match} is {df[best_match].mean():.2f}"

        if "max" in q or "highest" in q:
            return f"The maximum {best_match} is {df[best_match].max():.2f}"

        if "min" in q or "lowest" in q:
            return f"The minimum {best_match} is {df[best_match].min():.2f}"

        if "sum" in q:
            return f"The total {best_match} is {df[best_match].sum():.2f}"

        if "count" in q:
            return f"The count of {best_match} is {df[best_match].count()}"

    # =========================
    # 🎯 CATEGORICAL ANSWERS
    # =========================
    else:

        if "count" in q or "distribution" in q:
            counts = df[best_match].value_counts().head(5)
            return f"Top values in {best_match}:\n{counts.to_string()}"

        if "unique" in q:
            return f"{best_match} has {df[best_match].nunique()} unique values"

    # =========================
    # 🎯 DEFAULT RESPONSE
    # =========================
    return f"I found column '{best_match}'. Try asking average, max, min, count, or distribution."
st.set_page_config(page_title="GenAI Data Analyst", layout="wide")

st.title("GenAI Data Analyst")

# =========================
# 🧭 SIDEBAR NAVIGATION
# =========================
page = st.sidebar.radio("Navigation", [
    "Upload Data",
    "Overview",
    "Analysis",
    "Insights",
    "Ask Questions",
    "Report"
])

# =========================
# 📂 LOAD FILE
# =========================
if "df" not in st.session_state:
    st.session_state.df = None

if page == "Upload Data":
    uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            st.session_state.df = pd.read_csv(uploaded_file)
        else:
            st.session_state.df = pd.read_excel(uploaded_file)

        st.success("File uploaded successfully")

# =========================
# CHECK DATA
# =========================
df = st.session_state.df

if df is None and page != "Upload Data":
    st.warning("Please upload data first")
    st.stop()

# =========================
# 📊 OVERVIEW
# =========================
if page == "Overview":

    st.subheader("Quick Metrics")

    c1, c2, c3 = st.columns(3)

    c1.metric("Rows", df.shape[0])
    c2.metric("Columns", df.shape[1])
    c3.metric("Missing Values", df.isnull().sum().sum())

    st.subheader("Data Preview")
    st.dataframe(df.head(), use_container_width=True)

    # =========================
    # 🔍 DATA FILTER
    # =========================
    st.subheader("Filter Data")

    filter_col = st.selectbox("Select column to filter", df.columns)
    filter_val = st.text_input("Enter value to search")

    filtered_df = df  # ✅ default (VERY IMPORTANT)

    if filter_val:
        filtered_df = df[df[filter_col].astype(str).str.contains(filter_val, case=False)]

    st.write(f"Filtered Rows: {filtered_df.shape[0]}")
    st.dataframe(filtered_df.head(), use_container_width=True)
    col1, col2 = st.columns(2)
    col1.write(f"Shape: {df.shape}")
    col2.write("Columns:")
    col2.write(list(df.columns))

    st.subheader("Missing Values")
    missing = df.isnull().sum()
    missing = missing[missing > 0]

    if len(missing) > 0:
        st.write(missing)
    else:
        st.success("No missing values found")
    st.subheader("Missing Values (%)")
    st.write((df.isnull().mean() * 100).round(2))

# =========================
# 📈 ANALYSIS
# =========================
elif page == "Analysis":

    st.subheader("Statistical Summary")
    st.dataframe(df.describe(), use_container_width=True)

    numeric_cols = df.select_dtypes(include='number').columns

    # LINE CHART
    st.subheader("Trend Analysis")
    st.line_chart(df[numeric_cols])

    # HEATMAP
    st.subheader("Correlation Heatmap")
    corr = df[numeric_cols].corr()

    fig, ax = plt.subplots()
    cax = ax.matshow(corr, cmap="coolwarm")
    fig.colorbar(cax)

    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=90)
    ax.set_yticklabels(corr.columns)

    st.pyplot(fig)

    # HISTOGRAM
    st.subheader("Distribution")
    col = st.selectbox("Select Column", numeric_cols)

    fig, ax = plt.subplots()
    ax.hist(df[col], bins=20)
    st.pyplot(fig)

    # 🔥 BOXPLOT
    st.subheader("Boxplot Analysis")

    col_box = st.selectbox("Select column for boxplot", numeric_cols)

    fig, ax = plt.subplots()
    ax.boxplot(df[col_box])
    ax.set_title(f"Boxplot of {col_box}")

    st.pyplot(fig)

    # PIE CHART
    st.subheader("Category Distribution")

    cat_cols = df.select_dtypes(exclude='number').columns

    if len(cat_cols) > 0:
        col = st.selectbox("Select Categorical Column", cat_cols)

        counts = df[col].value_counts()

        fig, ax = plt.subplots()
        ax.pie(counts, labels=counts.index, autopct="%1.1f%%")
        st.pyplot(fig)
    else:
        st.info("No categorical columns")

# =========================
# 🔥 INSIGHTS
# =========================
elif page == "Insights":

    st.subheader("Key Insights")

    numeric_cols = df.select_dtypes(include='number').columns

    for col in numeric_cols:
        avg = df[col].mean()
        std = df[col].std()

        st.write(f"• {col.replace('_',' ')} average is {avg:.2f}")

        if std > avg * 0.5:
            st.write(f"  → High variation observed in {col}")
        else:
            st.write(f"  → Data is relatively stable for {col}")

    if len(numeric_cols) > 1:
        corr = df[numeric_cols].corr().abs()

        for i in range(len(corr)):
            corr.iloc[i, i] = 0

        pair = corr.unstack().idxmax()
        val = corr.unstack().max()

        st.write(f"\n• Strongest relationship between {pair[0]} and {pair[1]} (correlation {val:.2f})")

        if val > 0.7:
            st.write("  → Strong dependency detected")
        elif val > 0.4:
            st.write("  → Moderate relationship")
        else:
            st.write("  → Weak relationship")
# =========================
# 💬 Q&A
# =========================
# =========================
# 💬 ASK QUESTIONS PAGE
# =========================
elif page == "Ask Questions":

    st.subheader("Ask Questions About Data")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    col1, col2 = st.columns([5,1])

    with col1:
        question = st.text_input("Enter your question")

    with col2:
        ask_btn = st.button("Ask")

    if ask_btn and question:
        answer = ask_question(df, question)
        st.session_state.chat_history.append((question, answer))

    # latest answer
    if st.session_state.chat_history:
        st.subheader("Answer")
        st.success(st.session_state.chat_history[-1][1])

    # clear chat
    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

    # history
    st.subheader("Chat History")
    for q, a in reversed(st.session_state.chat_history):
        st.write(f"**Question:** {q}")
        st.write(f"Answer: {a}")
# =========================
# 📥 REPORT DOWNLOAD
# =========================
elif page == "Report":

    st.subheader("Download Full PDF Report")

    if st.button("Generate PDF Report"):

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=10)

        temp_dir = tempfile.gettempdir()

        # =========================
        # PAGE 1: TITLE
        # =========================
        pdf.add_page()
        pdf.set_font("Arial", "B", 18)
        pdf.cell(200, 10, "GenAI Data Analyst Report", ln=True, align="C")

        pdf.ln(10)
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 8, f"Shape: {df.shape}", ln=True)
        pdf.multi_cell(0, 8, f"Columns: {', '.join(df.columns)}")

        # =========================
        # PAGE 2: INSIGHTS
        # =========================
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "Key Insights", ln=True)

        pdf.set_font("Arial", size=11)

        numeric_cols = df.select_dtypes(include='number').columns

        for col in numeric_cols:
            if "id" not in col.lower():
                pdf.cell(200, 8, f"Average {col} = {df[col].mean():.2f}", ln=True)

        # correlation insight
        if len(numeric_cols) > 1:
            corr = df[numeric_cols].corr().abs()
            for i in range(len(corr)):
                corr.iloc[i, i] = 0

            pair = corr.unstack().idxmax()
            val = corr.unstack().max()

            pdf.ln(5)
            pdf.multi_cell(0, 8,
                f"Strongest relationship between {pair[0]} and {pair[1]} (correlation {val:.2f})"
            )

        # =========================
        # PAGE 3: TREND (FIXED)
        # =========================
        valid_cols = [c for c in numeric_cols if "id" not in c.lower()]
        top_cols = valid_cols[:3]

        plt.figure(figsize=(8, 4))
        df[top_cols].plot()
        plt.title("Trend Analysis")
        plt.xlabel("Index")
        plt.ylabel("Values")
        plt.legend()
        plt.grid(alpha=0.3)

        trend_path = os.path.join(temp_dir, "trend.png")
        plt.savefig(trend_path, bbox_inches='tight')
        plt.close()

        pdf.add_page()
        pdf.cell(200, 10, "Trend Analysis", ln=True)
        pdf.image(trend_path, w=180)

        # =========================
        # PAGE 4: HEATMAP (FIXED)
        # =========================
        import seaborn as sns

        plt.figure(figsize=(6, 5))
        sns.heatmap(df[valid_cols].corr(), annot=True, cmap="coolwarm")
        plt.title("Correlation Heatmap")

        heatmap_path = os.path.join(temp_dir, "heatmap.png")
        plt.savefig(heatmap_path, bbox_inches='tight')
        plt.close()

        pdf.add_page()
        pdf.cell(200, 10, "Correlation Heatmap", ln=True)
        pdf.image(heatmap_path, w=180)

        # =========================
        # HISTOGRAMS (ALL COLUMNS)
        # =========================
        for col in valid_cols:

            plt.figure(figsize=(6, 4))
            plt.hist(df[col], bins=20)
            plt.title(f"Distribution of {col}")
            plt.xlabel(col)
            plt.ylabel("Frequency")
            plt.grid(alpha=0.3)

            hist_path = os.path.join(temp_dir, f"{col}.png")
            plt.savefig(hist_path, bbox_inches='tight')
            plt.close()

            pdf.add_page()
            pdf.set_font("Arial", "B", 12)
            pdf.cell(200, 10, f"Distribution: {col}", ln=True)

            pdf.set_font("Arial", size=10)
            pdf.cell(200, 8,
                f"Mean: {df[col].mean():.2f} | Min: {df[col].min():.2f} | Max: {df[col].max():.2f}",
                ln=True
            )

            pdf.image(hist_path, w=180)

        # =========================
        # PIE CHART
        # =========================
        cat_cols = df.select_dtypes(exclude='number').columns

        if len(cat_cols) > 0:
            col = cat_cols[0]
            counts = df[col].value_counts()

            # 🔥 IMPORTANT FIX
            fig, ax = plt.subplots(figsize=(5, 5))   # create fresh figure

            ax.pie(counts, labels=counts.index, autopct='%1.1f%%')
            ax.set_title(f"{col} Distribution")

            pie_path = os.path.join(temp_dir, "pie.png")

            fig.savefig(pie_path, format="png", bbox_inches='tight')  # force PNG
            plt.close(fig)  # close properly

            pdf.add_page()
            pdf.cell(200, 10, f"{col} Distribution", ln=True)
            pdf.image(pie_path, w=150)

        # =========================
        # FINAL PAGE
        # =========================
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "Conclusion", ln=True)

        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 8,
            "This report provides insights into dataset trends, distributions, and relationships. "
            "These insights can help in understanding patterns and making informed decisions."
        )

        pdf_path = os.path.join(temp_dir, "report.pdf")
        pdf.output(pdf_path)

        with open(pdf_path, "rb") as f:
            st.download_button("Download PDF", f, file_name="GenAI_Report.pdf")