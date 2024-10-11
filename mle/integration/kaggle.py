import os
import json
import requests
import questionary
from zipfile import ZipFile


class KaggleIntegration:

    def __init__(self):
        """
        Initializes KaggleIntegration with the provided credentials.
        """

        kaggle_file = os.path.join(os.path.expanduser("~"), ".kaggle", "kaggle.json")

        if not os.path.exists(kaggle_file):
            username = questionary.text("What is your Kaggle username?").ask()
            key = questionary.password("What is your Kaggle token?").ask()
            if username and key:
                os.makedirs(os.path.dirname(kaggle_file), exist_ok=True)
                with open(kaggle_file, "w") as f:
                    json.dump({"username": username, "key": key}, f)

        from kaggle.api.kaggle_api_extended import KaggleApi
        self.api = KaggleApi()
        self.api.authenticate()

    def list_competition(self):
        """
        Lists all Kaggle competitions.
        :return: A tuple containing references of all competitions.
        """
        competitions = self.api.competitions_list()
        return tuple([comp.ref for comp in competitions])

    def download_competition_dataset(
            self, competition: str, download_dir: str = "./data"
    ):
        """
        Downloads and extracts the dataset for a specific competition.
        :param competition: The URL or name of the Kaggle competition.
        :param download_dir: Directory to save the downloaded files. Defaults to './data'.
        :return: The directory where the dataset has been downloaded and extracted.
        """
        if competition.startswith("https://www.kaggle.com/competitions/"):
            competition = competition.split("/")[-1]

        os.makedirs(download_dir, exist_ok=True)
        self.api.competition_download_files(competition, path=download_dir)

        # Unzip downloaded files
        for file in os.listdir(download_dir):
            if file.endswith(".zip"):
                with ZipFile(os.path.join(download_dir, file), "r") as zip_ref:
                    zip_ref.extractall(download_dir)
        return download_dir

    def fetch_competition_overview(self, competition: str):
        """
        Fetches competition overview information using the Kaggle API.
        :param competition: The URL or name of the Kaggle competition.
        :return: A dictionary containing competition overview information, or None if not found.
        """
        overview = None
        for _ in range(3):  # Retry 3 times if the request fails
            try:
                reader_url = f"https://r.jina.ai/{competition}/{overview}"
                response = requests.get(reader_url)
                response.raise_for_status()
                overview = response.text
            except requests.exceptions.HTTPError:
                continue
        return overview.encode('utf-8', 'ignore').decode('utf-8')
