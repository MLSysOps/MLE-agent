import os
import pandas as pd

from instructor import OpenAISchema
from pydantic import Field


def read_csv_file(file_path, limit=None, column_only=False):
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
        print("File does not exist.")
        return None


class ReadPathFunc(OpenAISchema):
    """
    Given a path to a code file, the function will read the raw content of the code file and return it.
    If the user provides a directory path, the function will return the list of files in the directory.
    """

    file_path: str = Field(
        ...,
        example='/Users/home/desktop/project/read_s3_data.py',
        descriptions="read the content of read_s3_data.py",
    )

    class Config:
        title = "read_path_content"

    @classmethod
    def execute(cls, file_path):
        if os.path.isfile(file_path):
            with open(file_path, 'r') as file:
                return file.read()
        elif os.path.isdir(file_path):
            return os.listdir(file_path)
        else:
            return "Invalid path provided."
