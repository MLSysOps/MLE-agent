import os
import json
import requests
import importlib
import questionary

from zipfile import ZipFile


def kaggle_login():
    """
    Kaggle login by retrieving the username and API key.
    :returns: A tuple containing the Kaggle username and API key.
    """
    kaggle_file = os.path.join(os.path.expanduser("~"), ".kaggle", "kaggle.json")

    try:
        with open(kaggle_file, "r") as f:
            kaggle_data = json.load(f)
        if questionary.confirm(
                f"Find the kaggle token in `{kaggle_file}` "
                f"(username: {kaggle_data['username']}).\n"
                "Would you like to integrate this token?"
        ).ask():
            return kaggle_data["username"], kaggle_data["key"]
    except FileNotFoundError:
        pass

    # login by manual input token
    username = questionary.text("What is your Kaggle username?").ask()
    key = questionary.password("What is your Kaggle key?").ask()
    return username, key


class KaggleIntegration:

    def __init__(self, username: str, token: str):
        """
        Initializes KaggleIntegration with the provided credentials.
        :param username: Kaggle username.
        :param token: Kaggle API key.
        """
        os.environ["KAGGLE_USERNAME"] = username
        os.environ["KAGGLE_KEY"] = token

        dependency = "kaggle"
        spec = importlib.util.find_spec(dependency)
        if spec is not None:
            self.client = importlib.import_module(dependency).api
        else:
            raise ImportError(
                "It seems you didn't install kaggle. In order to enable the Kaggle related features, "
                "please make sure kaggle Python package has been installed. "
                "More information, please refer to: https://www.kaggle.com/docs/api"
            )

    def list_competition(self):
        """
        Lists all Kaggle competitions.
        :return: A tuple containing references of all competitions.
        """
        competitions = self.client.competitions_list()
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
        self.client.competition_download_files(competition, path=download_dir)

        # Unzip downloaded files
        for file in os.listdir(download_dir):
            if file.endswith(".zip"):
                with ZipFile(os.path.join(download_dir, file), "r") as zip_ref:
                    zip_ref.extractall(download_dir)
        return download_dir

    def get_competition_overview(self, competition: str):
        """
        Fetches competition content using Jina Reader and returns it as a dictionary.
        :param competition: The URL or name of the Kaggle competition.
        """
        SECTIONS = ["overview", "data"]
        text_dict = {}
        for section in SECTIONS:
            for _ in range(3):  # Retry 3 times if the request fails
                try:
                    reader_url = f"https://r.jina.ai/{competition}/{section}"
                    response = requests.get(reader_url)
                    response.raise_for_status()
                    text_dict[section] = response.text
                except requests.exceptions.HTTPError:
                    continue
        return {
            "url": competition,
            "overview": text_dict["overview"],
            "data": text_dict["data"],
        }
