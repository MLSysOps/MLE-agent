import pandas as pd


def preview_csv_data(path: str, limit_rows: int = 5):
    """
    Preview the sample dataset from the project data path.
    :param path: the path to a local CSV file.
    :param limit_rows: the number of rows to preview.
    :return: the sample dataset.
    """
    df = pd.read_csv(path)
    df_limited = df.head(limit_rows)
    return df_limited.to_string(index=False)
