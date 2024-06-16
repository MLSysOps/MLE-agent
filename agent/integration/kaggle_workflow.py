import os
from zipfile import ZipFile

import requests
import pandas as pd
import questionary
import kaggle

from ..function import LeaderAgent
from ..function.plan_agent import gen_file_name
from ..utils import update_project_state, show_panel, Config

config = Config()


def url_to_text(url: str):
    """
    Fetches content from the given URL using Jina Reader and returns it as a dictionary.
    """
    SECTIONS = ["overview", "data"]
    text_dict = {}
    for section in SECTIONS:
        reader_url = f"https://r.jina.ai/{url}/{section}"
        response = requests.get(reader_url)
        response.raise_for_status()
        text_dict[section] = response.text
    return text_dict


class KaggleAgent(LeaderAgent):
    def __init__(self, project, model):
        super().__init__(project, model)
        self.kaggle_competition = self.project.kaggle_competition

    def authenticate_kaggle(self):
        kaggle_config = self.project.kaggle_config
        os.environ['KAGGLE_USERNAME'] = kaggle_config['username']
        os.environ['KAGGLE_KEY'] = kaggle_config['key']
        self.console.log(f"Authenticated with Kaggle as {kaggle_config['username']}")

    def select_competition(self):
        competitions = kaggle.api.competitions_list()
        competition_names = [comp.ref for comp in competitions]
        selected_competition = questionary.select(
            "Please select a Kaggle competition to join:",
            choices=competition_names
        ).ask()
        self.console.log(f"Selected competition: {selected_competition}")
        return selected_competition

    def fetch_competition_overview(self, selected_competition):
        competition_url = selected_competition
        overview_data = url_to_text(competition_url)
        requirements = overview_data.get('overview', 'No overview available')
        self.console.log(f"Competition requirements:\n{requirements}")
        return requirements

    def download_competition_dataset(self, selected_competition):
        project_data_path = os.path.join(self.project_home, 'data')
        os.makedirs(project_data_path, exist_ok=True)

        if selected_competition.startswith("https://www.kaggle.com/competitions/"):
            selected_competition = selected_competition.split('/')[-1]

        kaggle.api.competition_download_files(selected_competition, path=project_data_path)
        self.console.log(f"Dataset for {selected_competition} downloaded to {project_data_path}")

        # Unzip downloaded files
        for file in os.listdir(project_data_path):
            if file.endswith('.zip'):
                with ZipFile(os.path.join(project_data_path, file), 'r') as zip_ref:
                    zip_ref.extractall(project_data_path)
                os.remove(os.path.join(project_data_path, file))
        return project_data_path

    def sample_dataset(self, project_data_path):
        csv_files = [f for f in os.listdir(project_data_path) if f.endswith('.csv')]
        sample_data = None
        if csv_files:
            sample_file = csv_files[0]
            sample_data = pd.read_csv(os.path.join(project_data_path, sample_file)).head()
            self.console.print(f"Sample data from {sample_file}:\n{sample_data}")
        return sample_data

    def kaggle_requirements_understanding(self, selected_competition):
        show_panel("STEP 0: Kaggle Requirements Understanding")
        requirements = self.fetch_competition_overview(selected_competition)

        self.project.requirement = requirements
        self.project.enhanced_requirement = self.project.requirement

        if self.entry_file is None:
            self.entry_file = gen_file_name(self.project, self.model)
        self.console.print(f"[cyan]Entry File:[/cyan] {self.entry_file}")
        update_project_state(self.project)

    def start_kaggle_project(self):
        self.authenticate_kaggle()

        # STEP 0: Kaggle Requirements Understanding
        if self.project.kaggle_competition:
            self.console.print(f"[cyan]Kaggle Competition:[/cyan] {self.project.kaggle_competition}")
            self.console.print(f"[cyan]User Requirement:[/cyan] {self.project.requirement}")
        else:
            self.kaggle_competition = self.select_competition()
            self.project.kaggle_competition = self.kaggle_competition
            update_project_state(self.project)
            self.kaggle_requirements_understanding(self.kaggle_competition)

        # STEP 1: Dataset Preparation
        project_data_path = self.download_competition_dataset(self.project.kaggle_competition)
        sample_data = self.sample_dataset(project_data_path)
        if sample_data is not None:
            self.project.enhanced_requirement += f"\nDataset Sample: {sample_data.to_string()}"

        self.project.plan.dataset = project_data_path

        update_project_state(self.project)

    def invoke(self):
        """
        Execute the chain with Kaggle-specific steps.
        """
        try:
            self.start_kaggle_project()

            self.task_model_selection()
            self.task_planning()
            self.code_generation()
            self.execution_and_reflection()
            self.console.log("The chain has been completed.")
        except KeyboardInterrupt:
            self.console.log("MLE Plan Agent has been interrupted.")
            return
