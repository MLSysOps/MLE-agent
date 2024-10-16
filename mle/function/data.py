import textwrap
import pandas as pd
from pandas.api.types import is_numeric_dtype


def preview_csv_data(path: str, limit_rows: int = 5) -> str:
    """
    Preview the sample dataset from the project data path and include metadata.
    Refer to: https://github.com/WecoAI/aideml/blob/main/aide/utils/data_preview.py
    :param path: the path to a local CSV file.
    :param limit_rows: the number of rows to preview.
    :return: the sample dataset with metadata as a string.
    """
    try:
        df = pd.read_csv(path)
        num_rows, num_cols = df.shape
        summary = [f"-> {path} has {num_rows} rows and {num_cols} columns."]
        summary.append("Here is some information about the columns:")
        for col in sorted(df.columns):
            dtype = df[col].dtype
            name = f"{col} ({dtype})"
            nan_count = df[col].isnull().sum()
            if dtype == "bool":
                true_percentage = df[col].mean() * 100
                summary.append(f"{name} is {true_percentage:.2f}% True, {100 - true_percentage:.2f}% False")
            elif df[col].nunique() < 10:
                unique_values = df[col].unique().tolist()
                summary.append(f"{name} has {df[col].nunique()} unique values: {unique_values}")
            elif is_numeric_dtype(df[col]):
                min_val, max_val = df[col].min(), df[col].max()
                summary.append(f"{name} has range: {min_val:.2f} - {max_val:.2f}, {nan_count} NaN values")
            elif dtype == "object":
                unique_count = df[col].nunique()
                example_values = df[col].value_counts().head(limit_rows).index.tolist()
                summary.append(f"{name} has {unique_count} unique values. Some example values: {example_values}")
        return textwrap.dedent("\n".join(summary)).strip()
    except Exception as e:
        return f"cannot read csv data: {e}"
