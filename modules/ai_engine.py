def generate_insights(df):
    numeric = df.select_dtypes(include='number')

    insights = []

    for col in numeric.columns:
        insights.append(f"- Average {col} is {numeric[col].mean():.2f}")

    if len(numeric.columns) > 1:
        corr = numeric.corr().abs()

        for i in range(len(corr)):
            corr.iloc[i, i] = 0

        pair = corr.unstack().idxmax()
        val = corr.unstack().max()

        insights.append(
            f"- Strong relationship between {pair[0]} and {pair[1]} ({val:.2f})"
        )

    return "\n".join(insights)


def ask_question(df, question):
    q = question.lower()

    numeric = df.select_dtypes(include='number')

    # average
    if "average" in q:
        for col in numeric.columns:
            if col.lower() in q:
                return f"Average {col} is {numeric[col].mean():.2f}"

        return f"Average {numeric.columns[0]} is {numeric.iloc[:,0].mean():.2f}"

    # correlation
    if "correlation" in q or "relationship" in q:
        corr = numeric.corr().abs()

        for i in range(len(corr)):
            corr.iloc[i, i] = 0

        pair = corr.unstack().idxmax()
        val = corr.unstack().max()

        return f"Strongest relationship is between {pair[0]} and {pair[1]} ({val:.2f})"

    return "Try asking about averages or relationships."