import os

import pandas as pd


def csv_sample_dataset(project_data_path):
    csv_files = [f for f in os.listdir(project_data_path) if f.endswith('.csv')]
    sample_data = None
    if csv_files:
        sample_file = csv_files[0]
        sample_data = pd.read_csv(os.path.join(project_data_path, sample_file)).head()
    return sample_data
