import pandas as pd

# =========================
# 🤖 AI INSIGHTS (SMART RULE BASED)
# =========================
def generate_insights(df, mode="normal"):

    numeric_cols = df.select_dtypes(include='number').columns

    insights = []

    for col in numeric_cols:
        mean_val = df[col].mean()
        insights.append(f"Average {col.replace('_',' ')} is {mean_val:.2f}")

    # correlation insight
    if len(numeric_cols) > 1:
        corr = df[numeric_cols].corr().abs()
        pairs = corr.unstack().sort_values(ascending=False)
        pairs = pairs[pairs < 1]

        top = pairs.index[0]
        val = pairs.iloc[0]

        insights.append(
            f"Strong relationship between {top[0]} and {top[1]} (correlation {val:.2f})"
        )

    # style adjustment
    if mode == "beginner":
        insights = [f"{i}." for i in insights]

    elif mode == "business":
        insights = [f"Insight: {i}." for i in insights]

    # return bullets
    return "\n".join([f"- {i}" for i in insights])


# =========================
# 💬 Q&A FUNCTION (SMART MATCHING)
# =========================
def ask_question(df, question):
    q = question.lower()

    # normalize
    q = q.replace("hours", "hour").replace("hrs", "hour")

    numeric_cols = df.select_dtypes(include='number').columns

    # clean column names
    col_map = {
        col: col.lower().replace("_", " ")
        for col in numeric_cols
    }

    # 🔥 universal keywords (covers ALL 3 datasets)
    keywords = [
        # student / AI dataset
        "study", "usage", "performance", "screen", "ai",

        # social dataset
        "sleep", "stress", "anxiety", "social",

        # health dataset
        "bmi", "age", "disease", "heart", "Diabetes",
        "Cancer", "Stroke", "kidney", "liver",
        "parkinson", "alzheimer", "copd", "tuberculosis"
    ]

    # =========================
    # 🔹 AVERAGE
    # =========================
    if any(word in q for word in ["average", "mean", "avg"]):

        best_match = None
        best_score = 0

        for col, clean in col_map.items():
            score = 0

            # word matching
            for word in clean.split():
                if word in q:
                    score += 1

            # keyword boost
            for k in keywords:
                if k in q and k in clean:
                    score += 2

            if score > best_score:
                best_score = score
                best_match = col

        if best_match:
            name = best_match.replace("_", " ").title()
            return f"The average {name} is {df[best_match].mean():.2f}."

    # =========================
    # 🔹 CORRELATION
    # =========================
    if "correlation" in q or "relationship" in q:

        if len(numeric_cols) > 1:
            corr = df[numeric_cols].corr().abs()

            for i in range(len(corr)):
                corr.iloc[i, i] = 0

            pair = corr.unstack().idxmax()
            val = corr.unstack().max()

            return f"The strongest relationship is between {pair[0]} and {pair[1]} (correlation {val:.2f})."

    # =========================
    # 🔹 HIGHEST / LOWEST
    # =========================
    if "highest" in q or "maximum" in q:
        col = df[numeric_cols].mean().idxmax()
        return f"{col.replace('_',' ').title()} has the highest average value."

    if "lowest" in q or "minimum" in q:
        col = df[numeric_cols].mean().idxmin()
        return f"{col.replace('_',' ').title()} has the lowest average value."

    # =========================
    # 🔹 SUMMARY
    # =========================
    if "summary" in q or "insight" in q:
        return df.describe().round(2).to_string()

    # =========================
    # ❌ FALLBACK
    # =========================
    sample_cols = ", ".join(df.columns[:5])
    return f"I couldn't match your question. Try asking about: {sample_cols}"