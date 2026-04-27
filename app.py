import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile
import os
import fitz  # PyMuPDF for PDF manipulation

def ask_question(df, question):

    q = question.lower()

    numeric_cols = df.select_dtypes(include='number').columns
    all_cols = df.columns

    # =========================
    # 📄 PDF TEXT MODE (UNSTRUCTURED)
    # =========================
    if "content" in df.columns:

        if "find" in q or "search" in q:
            results = df[df["content"].str.contains(q, case=False, na=False)]

            if len(results) > 0:
                return "Found:\n" + "\n".join(results["content"].head(5))
            else:
                return "No matching text found"

        return "PDF detected. Try: find <keyword> or search <word>."

    # =========================
    # 🔍 CLEAN COLUMN NAMES
    # =========================
    col_map = {col: col.lower().replace("_", " ") for col in all_cols}

    # =========================
    # 🔍 FIND MATCHING COLUMNS
    # =========================
    matches = []

    for col, clean in col_map.items():
        score = 0

        for word in clean.split():
            if word in q:
                score += 2

        if clean in q:
            score += 5

        if score > 0:
            matches.append((col, score))

    matches = sorted(matches, key=lambda x: x[1], reverse=True)

    # =========================
    # 🎯 GENERAL QUESTIONS
    # =========================
    if "summary" in q or "dataset" in q:
        return f"Dataset has {df.shape[0]} rows and {df.shape[1]} columns."

    if "columns" in q:
        return f"Columns are: {', '.join(df.columns)}"

    # =========================
    # 🎯 CORRELATION
    # =========================
    if "correlation" in q or "relationship" in q:
        if len(numeric_cols) > 1:
            corr = df[numeric_cols].corr().abs()
            for i in range(len(corr)):
                corr.iloc[i, i] = 0

            pair = corr.unstack().idxmax()
            val = corr.unstack().max()

            return f"Strongest relationship is between {pair[0]} and {pair[1]} (correlation {val:.2f})"
        else:
            return "Not enough numeric columns for correlation."

    # =========================
    # ❌ NO MATCH
    # =========================
    if len(matches) == 0:
        return f"No relevant column found. Available columns: {', '.join(df.columns)}"

    # =========================
    # 🎯 MULTI-COLUMN OPERATIONS
    # =========================
    if "average" in q or "mean" in q:
        results = [f"{col}: {df[col].mean():.2f}" for col, _ in matches if col in numeric_cols]
        if results:
            return "Averages:\n" + "\n".join(results[:5])

    if "max" in q or "highest" in q:
        results = [f"{col}: {df[col].max():.2f}" for col, _ in matches if col in numeric_cols]
        if results:
            return "Maximum values:\n" + "\n".join(results[:5])

    if "min" in q or "lowest" in q:
        results = [f"{col}: {df[col].min():.2f}" for col, _ in matches if col in numeric_cols]
        if results:
            return "Minimum values:\n" + "\n".join(results[:5])

    # =========================
    # 🔥 COMPARISON
    # =========================
    if "compare" in q or "difference" in q:
        if len(matches) >= 2:
            col1, col2 = matches[0][0], matches[1][0]

            if col1 in numeric_cols and col2 in numeric_cols:
                diff = abs(df[col1].mean() - df[col2].mean())
                return f"Difference between average {col1} and {col2} is {diff:.2f}"

        return "Please mention two numeric columns to compare."

    # =========================
    # 🎯 DISTRIBUTION
    # =========================
    if "count" in q or "distribution" in q:
        best = matches[0][0]
        counts = df[best].value_counts().head(5)
        return f"Top values in {best}:\n{counts.to_string()}"

    # =========================
    # 🎯 UNIQUE
    # =========================
    if "unique" in q:
        best = matches[0][0]
        return f"{best} has {df[best].nunique()} unique values"

    # =========================
    # 🎯 DEFAULT RESPONSE
    # =========================
    best = matches[0][0]

    if best in numeric_cols:
        return f"{best} → Avg: {df[best].mean():.2f}, Max: {df[best].max():.2f}, Min: {df[best].min():.2f}"
    else:
        return f"Column '{best}' detected. Try asking: average, max, distribution, compare."
    


st.set_page_config(page_title="GenAI Data Analyst", layout="wide")
st.markdown("""
<style>

/* ===== MAIN LAYOUT ===== */
.block-container {
    padding-top: 1rem;
    max-width: 1200px;
}

/* ===== HERO ===== */
.hero {
    background: linear-gradient(135deg, #0f172a, #1e40af);
    padding: 30px;
    border-radius: 18px;
    border: 1px solid #1f2937;
    margin-bottom: 25px;
}

.hero-title {
    font-size: 36px;
    font-weight: 700;
    color: white;
}

.hero-sub {
    color: #cbd5f5;
}

/* ===== KPI ===== */
.kpi {
    background: linear-gradient(135deg, #020617, #0f172a);
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #1f2937;
    text-align: center;
}

.kpi-title {
    color: #9ca3af;
}

.kpi-value {
    font-size: 22px;
    font-weight: bold;
    color: #e5e7eb;
}

/* ===== CARD ===== */
.card {
    background: #020617;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #1f2937;
    margin-bottom: 20px;
}

/* ===== BUTTON ===== */
.stButton>button {
    border-radius: 10px;
    background: linear-gradient(90deg, #2563eb, #1d4ed8);
    color: white;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div class="hero-title">GenAI Data Analyst</div>
    <div class="hero-sub">AI-powered insights, charts, and analysis</div>
</div>
""", unsafe_allow_html=True)
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
# LOAD FILE
# =========================
if "df" not in st.session_state:
    st.session_state.df = None

if page == "Upload Data":

    # =========================
    # 🎨 UI STYLE
    # =========================
    # =========================
    # 🎨 PREMIUM UI STYLE
    # =========================
    st.markdown("""
    <style>

    /* Page background spacing */
    .block-container {
        padding-top: 2rem;
    }

    /* Header Banner */
    .header-box {
        background: linear-gradient(135deg, #0f172a, #1e3a8a);
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 30px;
        border: 1px solid #334155;
    }

    .header-title {
        font-size: 40px;
        font-weight: 700;
        color: white;
    }

    .header-sub {
        color: #cbd5f5;
        font-size: 16px;
    }

    /* Upload Card */
    .upload-card {
        background: linear-gradient(135deg, #1e293b, #020617);
        padding: 40px;
        border-radius: 18px;
        border: 1px solid #334155;
        text-align: center;
        transition: 0.3s ease;
    }

    .upload-card:hover {
        border: 1px solid #3b82f6;
        box-shadow: 0 0 20px rgba(59,130,246,0.3);
    }

    /* Title */
    .upload-title {
        font-size: 28px;
        font-weight: 600;
        margin-bottom: 10px;
    }

    /* Subtitle */
    .upload-sub {
        color: #94a3b8;
        margin-bottom: 25px;
    }

    /* Success / Info spacing */
    .stAlert {
        border-radius: 10px;
    }

    </style>
    """, unsafe_allow_html=True)


    # =========================
    # 🚀 HEADER
    # =========================



    # =========================
    # 📦 UPLOAD CARD
    # =========================


    st.markdown("""
    <div class="upload-card">
        <div class="card-title">Upload Your Dataset</div>
        <p style="color:#9ca3af;">Supports CSV, Excel, and TXT files</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="upload-sub">Supports CSV, Excel, and TXT files</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        " ",
        type=["csv", "xlsx", "txt", "pdf"],
        label_visibility="collapsed"
    )

    st.markdown('</div>', unsafe_allow_html=True)


    # =========================
    # 🔧 FILE LOGIC (KEEP SAME)
    # =========================
    if uploaded_file:

        df = None

        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)

            elif uploaded_file.name.endswith(".xlsx"):
                df = pd.read_excel(uploaded_file)

            elif uploaded_file.name.endswith(".txt"):

                try:
                    df = pd.read_csv(uploaded_file, sep=None, engine='python')

                except:
                    try:
                        df = pd.read_csv(uploaded_file, sep=",", on_bad_lines='skip')
                        st.warning("Some rows skipped due to formatting")

                    except:
                        try:
                            df = pd.read_csv(uploaded_file, sep="\t", on_bad_lines='skip')
                            st.warning("Some rows skipped due to formatting")

                        except:
                            st.error("Could not read TXT file. Please check format.")

            elif uploaded_file.name.endswith(".pdf"):

                try:
                    uploaded_file.seek(0)

                    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

                    text = ""
                    for page in doc:
                        text += page.get_text()

                    lines = [line.strip() for line in text.split("\n") if line.strip()]

                    # =========================
                    # 🔥 DETECT FORMAT
                    # =========================

                    # CASE 1: CSV-style PDF
                    if "," in lines[0]:

                        from io import StringIO

                        csv_text = "\n".join(lines)
                        df = pd.read_csv(StringIO(csv_text))

                        st.success("CSV-style PDF detected and loaded")

                    # CASE 2: key:value PDF
                    else:

                        data = []

                        for line in lines:
                            row = {}

                            parts = line.split(",")

                            for part in parts:
                                if ":" in part:
                                    key, val = part.split(":", 1)
                                    row[key.strip()] = val.strip()

                            if row:
                                data.append(row)

                        df = pd.DataFrame(data)

                        # convert numeric
                        for col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors="ignore")

                        st.success("Text PDF converted to structured dataset")

                except Exception as e:
                    st.error(f"Error reading PDF: {e}")
        except Exception as e:
            st.error(f"Error reading file: {e}")

        if df is not None:
            st.session_state.df = df
            st.success("File uploaded successfully")
            st.info(f"Rows: {df.shape[0]} | Columns: {df.shape[1]}")
            st.dataframe(df.head(), use_container_width=True)
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

    st.markdown('<div class="card">', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div class="kpi">
            <div class="kpi-title">Rows</div>
            <div class="kpi-value">{df.shape[0]}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="kpi">
            <div class="kpi-title">Columns</div>
            <div class="kpi-value">{df.shape[1]}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="kpi">
            <div class="kpi-title">Missing</div>
            <div class="kpi-value">{df.isnull().sum().sum()}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
        

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

    numeric_cols = df.select_dtypes(include='number').columns

    if len(numeric_cols) == 0:
        st.warning("No numeric columns available (PDF/text data detected)")
    else:
        col = st.selectbox("Select Column", list(numeric_cols), key="hist_col")

        if col in df.columns:
            fig, ax = plt.subplots()
            ax.hist(df[col].dropna(), bins=20)

            ax.set_title(f"Distribution of {col}")
            ax.set_xlabel(col)
            ax.set_ylabel("Frequency")

            st.pyplot(fig)

        

    # 🔥 BOXPLOT
    st.subheader("Boxplot Analysis")

    if len(numeric_cols) == 0:
        st.warning("No numeric columns for boxplot")
    else:
        col_box = st.selectbox("Select column for boxplot", list(numeric_cols), key="box_col")

        if col_box in df.columns:
            fig, ax = plt.subplots()
            ax.boxplot(df[col_box].dropna())

            ax.set_title(f"Boxplot of {col_box}")

            st.pyplot(fig)

    # PIE CHART
    st.subheader("Category Distribution")

    cat_cols = df.select_dtypes(exclude='number').columns

    if len(cat_cols) == 0:
        st.info("No categorical columns available")
    else:
        col_cat = st.selectbox("Select Categorical Column", list(cat_cols), key="pie_col")

        if col_cat in df.columns:
            counts = df[col_cat].value_counts().head(6)

            fig, ax = plt.subplots()
            ax.pie(counts, labels=counts.index, autopct="%1.1f%%")

            ax.set_title(f"Distribution of {col_cat}")

            st.pyplot(fig)

# =========================
# 🔥 INSIGHTS
# =========================
elif page == "Insights":

    st.subheader("Key Insights")

    numeric_cols = df.select_dtypes(include='number').columns

    # 🔥 HANDLE NO NUMERIC CASE (PDF)
    if len(numeric_cols) == 0:
        st.warning("No numeric data available for insights (PDF/text detected)")

        # fallback insight
        st.write(f"Dataset has {df.shape[0]} rows and {df.shape[1]} columns")

        st.write("Columns available:")
        st.write(list(df.columns))

        st.info("Upload structured data (CSV/Excel) or structured PDF for full insights")

        st.stop()
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