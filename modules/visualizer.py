import streamlit as st

def show_charts(df):
    numeric_df = df.select_dtypes(include='number')
    if not numeric_df.empty:
        st.line_chart(numeric_df)

def show_correlation(corr):
    st.subheader("Correlation Matrix")
    st.write(corr)