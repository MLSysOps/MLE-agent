import os
import py7zr
import gzip
import bz2
import lzma
import shutil
import tarfile
import zipfile
import textwrap
import pandas as pd
from pandas.api.types import is_numeric_dtype


def unzip_data(compressed_file_path: str, extract_path: str):
    """
    Unzip a compressed file, supporting various formats (.zip, .7z, .tar, .gz, .bz2, .xz).

    :param compressed_file_path: Path to the compressed file
    :param extract_path: Path where the contents will be extracted
    :return: String with the path to the unzipped contents
    """
    if not os.path.exists(compressed_file_path):
        raise FileNotFoundError(f"The file {compressed_file_path} does not exist.")

    # Create the extraction directory if it doesn't exist
    os.makedirs(extract_path, exist_ok=True)

    file_extension = os.path.splitext(compressed_file_path)[1].lower()
    file_name = os.path.splitext(os.path.basename(compressed_file_path))[0]

    # Create a subdirectory with the name of the compressed file
    specific_extract_path = os.path.join(extract_path, file_name)
    os.makedirs(specific_extract_path, exist_ok=True)

    try:
        if file_extension == '.zip':
            with zipfile.ZipFile(compressed_file_path, 'r') as zip_ref:
                zip_ref.extractall(specific_extract_path)

        elif file_extension == '.7z':
            with py7zr.SevenZipFile(compressed_file_path, mode='r') as z:
                z.extractall(specific_extract_path)

        elif file_extension in ['.tar', '.gz', '.bz2', '.xz']:
            if file_extension == '.gz':
                open_func = gzip.open
            elif file_extension == '.bz2':
                open_func = bz2.open
            elif file_extension == '.xz':
                open_func = lzma.open
            else:
                open_func = open

            with open_func(compressed_file_path, 'rb') as f:
                if tarfile.is_tarfile(compressed_file_path) or file_extension in ['.gz', '.bz2', '.xz']:
                    with tarfile.open(fileobj=f) as tar:
                        tar.extractall(path=specific_extract_path)
                else:
                    # For single file compression (non-tar)
                    output_filename = os.path.splitext(os.path.basename(compressed_file_path))[0]
                    output_path = os.path.join(specific_extract_path, output_filename)
                    with open(output_path, 'wb') as out_f:
                        shutil.copyfileobj(f, out_f)

        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

        print(f"Successfully extracted {compressed_file_path} to {specific_extract_path}")
        return specific_extract_path

    except Exception as e:
        print(f"Error extracting {compressed_file_path}: {str(e)}")
        raise


def preview_zip_structure(zip_path, max_files=50, max_dirs=20, max_output_length=1000, show_hidden=False):
    """
    Preview the structure of a zip file with limits on output and option to show hidden files.
    :param zip_path: the path to the zip file.
    :param max_files: maximum number of files to display.
    :param max_dirs: maximum number of directories to display.
    :param max_output_length: maximum length of the output string.
    :param show_hidden: if True, show hidden files and directories (starting with a dot).
    :return: the limited structure of the zip file as a string.
    """
    if not os.path.exists(zip_path):
        return f"Error: The file '{zip_path}' does not exist."

    if not zipfile.is_zipfile(zip_path):
        return f"Error: '{zip_path}' is not a valid zip file."

    structure = []
    file_count = 0
    dir_count = 0
    total_count = 0
    hidden_count = 0

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            file_path = file_info.filename
            is_hidden = os.path.basename(file_path).startswith('.')

            if is_hidden and not show_hidden:
                hidden_count += 1
                continue

            if file_info.is_dir():
                if dir_count < max_dirs:
                    structure.append(f"Directory: {file_path}")
                    dir_count += 1
            else:
                if file_count < max_files:
                    structure.append(f"File: {file_path}")
                    file_count += 1

            total_count += 1
            if len("\n".join(structure)) >= max_output_length:
                structure.append("... (output truncated due to length)")
                break

    if file_count >= max_files:
        structure.append(f"... (and {total_count - file_count - dir_count} more files)")
    if dir_count >= max_dirs:
        structure.append(f"... (and {total_count - file_count - dir_count} more directories)")
    if not show_hidden and hidden_count > 0:
        structure.append(f"... ({hidden_count} hidden items not shown)")

    output = "\n".join(structure)
    if len(output) > max_output_length:
        output = output[:max_output_length] + "... (output truncated)"

    return output


def preview_csv_data(path: str, limit_rows: int = 5, limit_columns: int = None) -> str:
    """
    Preview the sample dataset from the project data path and include metadata.
    :param path: the path to a local CSV file.
    :param limit_rows: the number of rows to preview.
    :param limit_columns: the number of columns to preview. If None, all columns are previewed.
    :return: the sample dataset with metadata as a string.
    """
    try:
        df = pd.read_csv(path)
        num_rows, num_cols = df.shape
        summary = [f"CSV file in `{path}` has {num_rows} rows and {num_cols} columns."]

        if limit_columns is not None and limit_columns < num_cols:
            columns_to_preview = sorted(df.columns)[:limit_columns]
            summary.append(f"Previewing {limit_columns} out of {num_cols} columns.")
        else:
            columns_to_preview = sorted(df.columns)

        summary.append("Here is some information about the columns:")

        for col in columns_to_preview:
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
        return f"Cannot read CSV data: {e}"


if __name__ == "__main__":
    print(preview_zip_structure("/Users/huangyz0918/Downloads/stat202A_hw.zip"))
