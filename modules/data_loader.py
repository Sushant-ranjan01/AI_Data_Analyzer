import pandas as pd

def load_file(file):
    try:
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        elif file.name.endswith('.xlsx'):
            return pd.read_excel(file)
        else:
            return None
    except Exception:
        return None