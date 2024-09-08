import textwrap
import pandas as pd


def preview_csv_data(path: str, limit_rows: int = 1) -> str:
    """
    Preview the sample dataset from the project data path and include metadata.
    :param path: the path to a local CSV file.
    :param limit_rows: the number of rows to preview.
    :return: the sample dataset with metadata as a string.
    """
    try:
        df = pd.read_csv(path)
        num_rows = len(df)
        columns = ', '.join(df.columns)
        df_limited = df.head(limit_rows)
        data_dict_list = df_limited.to_dict(orient='records')
        data_dict_str = "\n".join([str(record) for record in data_dict_list])

        return textwrap.dedent(f"""
        Data file: {path}\nNumber of all rows: {num_rows}\nAll columns: {columns}\nData example:\n{data_dict_str}
        """).strip()
    except Exception as e:
        return f"cannot read csv data: {e}"
