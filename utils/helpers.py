def clean_text(df):
    summary = f"""
Dataset Summary:

Average Age: {df['age'].mean():.2f}
Average Daily Social Media Hours: {df['daily_social_media_hours'].mean():.2f}
Average Sleep Hours: {df['sleep_hours'].mean():.2f}
Average Stress Level: {df['stress_level'].mean():.2f}
Average Anxiety Level: {df['anxiety_level'].mean():.2f}
Average Academic Performance: {df['academic_performance'].mean():.2f}
Average Physical Activity: {df['physical_activity'].mean():.2f}
"""

    return summary


def get_correlation(df):
    corr = df.corr(numeric_only=True)
    return corr.to_string()