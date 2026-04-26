def basic_info(df):
    return {
        "shape": df.shape,
        "columns": list(df.columns),
        "missing": df.isnull().sum()
    }

def describe_data(df):
    return df.describe()

def correlation(df):
    return df.select_dtypes(include='number').corr()