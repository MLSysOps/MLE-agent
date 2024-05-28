import os

import pandas as pd


def read_csv_file(file_path, limit=3, column_only=False):
    """
    Reads a CSV file and returns a DataFrame with a limited number of rows or only column names.

    Parameters:
    - file_path (str): The path to the CSV file.
    - limit (int, optional): The number of rows to read from the CSV file. Defaults to None, which reads all rows.
    - column_only (bool, optional): If True, returns only the column names. Defaults to False.

    Returns:
    - DataFrame if the file exists and is read successfully and column_only is False.
    - List of column names if column_only is True.
    - None if the file does not exist.
    """
    if file_path is None:
        return None

    if os.path.exists(file_path):
        try:
            if column_only:
                df = pd.read_csv(file_path, nrows=1)
                return df.columns.tolist()
            elif limit is not None:
                return pd.read_csv(file_path, nrows=limit)
            else:
                return pd.read_csv(file_path)
        except Exception as e:
            print(f"Error reading the CSV file: {e}")
            return None
    else:
        return None
