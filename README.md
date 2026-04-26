# GenAI Data Analyst

A smart data analysis web application built using Streamlit that allows users to upload datasets, generate insights, and ask questions about data.

---

## Features

- Upload CSV or Excel datasets  
- Data preview and statistical summary  
- Correlation analysis and visualizations  
- Automatically generated insights  
- Question-answering system for datasets  
- Works with multiple datasets dynamically  
- Chat history support  

---

## How It Works

- Uses Pandas for data processing  
- Uses Streamlit for user interface  
- Uses a custom intelligent engine for:
  - detecting column names  
  - answering questions dynamically  
  - generating insights  

- Works across different datasets such as:
  - Social media dataset  
  - AI student dataset  
  - Health/disease dataset  

---

## Tech Stack

- Python  
- Streamlit  
- Pandas  
- Matplotlib / Seaborn  
- Transformers (optional AI component)  

---

## Installation

```bash
git clone https://github.com/Sushant-ranjan01/AI_Data_Analyzer.git
cd AI_Data_Analyzer
pip install -r requirements.txt
streamlit run app.py