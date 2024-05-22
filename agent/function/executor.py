import os
import yaml
import questionary
import sky


class Executor:
    def __init__(self, project_name: str, workdir: str):
        self.project_name = project_name
        self.workdir = workdir
        self.cluster_name = self.project_name + "_cluster"
        self.yml_name = self.project_name + ".yml"
        self.checkpoint_dir = "checkpoints"

    def task_setup_sec_generate(self):
        setup_commands = """\
set -e  # Exit if any command failed.
git clone https://github.com/huggingface/transformers/ || true
cd transformers
pip install .
cd examples/pytorch/text-classification
pip install -r requirements.txt torch==1.12.1+cu113 --extra-index-url https://download.pytorch.org/whl/cu113
"""
        return setup_commands

    def task_run_sec_generate(self):
        run_commands = """\
set -e  # Exit if any command failed.
cd transformers/examples/pytorch/text-classification
python run_glue.py \\
--model_name_or_path bert-base-cased \\
--dataset_name imdb  \\
--do_train \\
--max_seq_length 128 \\
--per_device_train_batch_size 32 \\
--learning_rate 2e-5 \\
--max_steps 50 \\
--output_dir /tmp/imdb/ --overwrite_output_dir \\
--fp16
"""
        return run_commands

    def task_yml_generate(self):
        """
        Prepare the task yml file for the project.
        """
        task_content = {
            'name': self.project_name,
            'resources': {
                'accelerators': 'V100:1'
            },
            'workdir': self.workdir,
            'setup': self.task_setup_sec_generate(),
            'run': self.task_run_sec_generate()
        }

        def str_presenter(dumper, data):
            if data.count('\n') > 0:  # Check for multiline string
                return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
            return dumper.represent_scalar('tag:yaml.org,2002:str', data)

        yaml.add_representer(str, str_presenter)

        with open(self.yml_name, 'w') as file:
            yaml.dump(task_content, file, sort_keys=False, default_flow_style=False)
        print(f"Task YAML file {self.yml_name} generated successfully.")

    def launch(self):
        """
        Launch the project with the given configuration and SkyPilot.
        """
        launch_type = questionary.select(
            "How do you want to launch this project?",
            choices=["remote", "local"]
        ).ask()

        if launch_type == "local":
            os.system(f"python {os.path.join(self.workdir, 'main.py')}")
        else:
            task = sky.Task.from_yaml(self.yml_name)
            sky.launch(task, cluster_name=self.cluster_name, idle_minutes_to_autostop=5, down=True)
            print(f"Project launched remotely on cluster {self.cluster_name}.")


if __name__ == "__main__":
    # Example usage
    project_name = "example_project"
    workdir = "./"

    executor = Executor(project_name, workdir)
    executor.task_yml_generate()
    executor.launch()
