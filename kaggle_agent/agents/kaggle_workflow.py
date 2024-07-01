import os
from zipfile import ZipFile

import kaggle
import questionary
from rich.console import Console

from agent.function import LeaderAgent
from agent.function.plan_agent import gen_file_name
from agent.tools import kaggle_url_to_text, csv_sample_dataset
from agent.utils import update_project_state, show_panel, Config

config = Config()


def pmpt_kaggle_req():
    return """
    You are a machine learning engineer tasked with understanding the requirements of a Kaggle competition step-by-step.
    
    Instructions:
    - You will be provided with the kaggle competition overview and data description.
    - You will need to understand them and provide a detailed summary of the competition by following the template.
    
    Output:
    The output must have the following format:
    
    Competition Requirements:
    
    Data Description:
    
    Evaluation Criteria:
    
    Submission Format:
    
    FAQ:
    """


def gen_kaggle_requirements(overview, data_desc, llm_Agent) -> str:
    """
    Generate a formatted string from the raw Kaggle requirements.
    """
    console = Console()
    prompt_message = pmpt_kaggle_req()

    raw_req = overview + '\n' + data_desc

    with console.status("Generating Kaggle requirements..."):
        chat_history = [
            {"role": 'system', "content": prompt_message},
            {"role": 'user', "content": raw_req}
        ]
        enhanced_req = llm_Agent.query(chat_history)

    return enhanced_req


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
        self.console.log(f"You must join a Kaggle competition on Kaggle.com to proceed.")
        selected_competition = questionary.select(
            "Please select a Kaggle competition to join:",
            choices=competition_names
        ).ask()
        self.console.log(f"Selected competition: {selected_competition}")
        return selected_competition

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

    def kaggle_requirements_understanding(self, selected_competition):
        show_panel("STEP 0: Kaggle Requirements Understanding")

        competition_url = selected_competition
        overview, data_desc = kaggle_url_to_text(competition_url)
        requirement = gen_kaggle_requirements(overview, data_desc, self.model)
        print(requirement)

        if requirement is None:
            raise ValueError("Kaggle requirements understanding failed.")

        self.console.log(f"{selected_competition} requirements: {requirement}")
        self.project.requirement = requirement
        self.project.enhanced_requirement = self.project.requirement

        if self.entry_file is None:
            self.entry_file = gen_file_name(self.project, self.model)
        self.console.print(f"[cyan]Entry File:[/cyan] {self.entry_file}")

    def start_kaggle_project(self):
        self.authenticate_kaggle()

        # STEP 0: Kaggle Requirements Understanding
        if self.project.kaggle_competition and self.project.requirement:
            self.console.print(f"[cyan]Kaggle Competition:[/cyan] {self.project.kaggle_competition}")
            self.console.print(f"[cyan]User Requirement:[/cyan] {self.project.requirement}")
        else:
            self.kaggle_competition = self.select_competition()
            self.project.kaggle_competition = self.kaggle_competition
            self.kaggle_requirements_understanding(self.kaggle_competition)
            update_project_state(self.project)

        # STEP 1: Dataset Preparation
        project_data_path = self.download_competition_dataset(self.project.kaggle_competition)

        # TODO: tool calling for the check of the datasets
        sample_data = csv_sample_dataset(project_data_path)
        self.console.print(f"Sample data from {project_data_path}:\n{sample_data}")

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
