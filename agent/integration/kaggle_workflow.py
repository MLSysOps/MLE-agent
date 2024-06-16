import os
import kaggle
import questionary
from rich.console import Console

console = Console()


def start_kaggle_project(kaggle_config):
    """
    Start a Kaggle project using the provided configuration.
    :param kaggle_config: Dictionary containing Kaggle username and API key.
    """
    os.environ['KAGGLE_USERNAME'] = kaggle_config['username']
    os.environ['KAGGLE_KEY'] = kaggle_config['key']

    console.log(f"Authenticated with Kaggle as {kaggle_config['username']}")

    # Example command to download a dataset (adjust as needed)
    dataset = questionary.text("Enter the Kaggle dataset to download (e.g., 'zillow/zecon'):").ask()
    kaggle.api.dataset_download_files(dataset, path='./data', unzip=True)
    console.log(f"Dataset {dataset} downloaded to ./data")