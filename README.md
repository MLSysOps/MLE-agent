<div align="center">
<h1 align="center">MLE-Agent: Your intelligent companion for seamless AI engineering and research.</h1>
<img alt="kaia-llama" height="200px" src="assets/kaia_llama.webp">
<a href="https://trendshift.io/repositories/11658" target="_blank"><img src="https://trendshift.io/api/badge/repositories/11658" alt="MLSysOps%2FMLE-agent | Trendshift" style="width: 250px; height: 200px;" width="250" height="200px"/></a>
<p align="center">:love_letter: Fathers' love for Kaia :love_letter:</p>

![](https://github.com/MLSysOps/MLE-agent/actions/workflows/lint.yml/badge.svg)
![](https://github.com/MLSysOps/MLE-agent/actions/workflows/test.yml/badge.svg)
![PyPI - Version](https://img.shields.io/pypi/v/mle-agent)
[![Downloads](https://static.pepy.tech/badge/mle-agent)](https://pepy.tech/project/mle-agent)
![GitHub License](https://img.shields.io/github/license/MLSysOps/MLE-agent)
<a href="https://discord.gg/d9vcY7PA8Z"><img src="https://img.shields.io/badge/Discord-Join%20Us-purple?logo=discord&logoColor=white&style=flat" alt="Join our Discord community"></a>

[📚 Docs](https://mle-agent-site.vercel.app/) |
[🐞 Report Issues](https://github.com/MLSysOps/MLE-agent/issues/new) |
👋 Join us on <a href="https://discord.gg/d9vcY7PA8Z" target="_blank">Discord</a>

</div>

## Overview

MLE-Agent is designed as a pairing LLM agent for machine learning engineers and researchers. It is featured by:

- 🤖 Autonomous Baseline: Automatically builds ML/AI baselines and solutions based on your requirements.
- 🏅End-to-end ML Task: Participates in Kaggle competitions and completes tasks independently.
- 🔍 [Arxiv](https://arxiv.org/) and [Papers with Code](https://paperswithcode.com/) Integration: Access best practices
  and state-of-the-art methods.
- 🐛 Smart Debugging: Ensures high-quality code through automatic debugger-coder interactions.
- 📂 File System Integration: Organizes your project structure efficiently.
- 🧰 Comprehensive Tools Integration: Includes AI/ML functions and MLOps tools for a seamless workflow.
- ☕ Interactive CLI Chat: Enhances your projects with an easy-to-use chat interface.
- 🧠 Smart Advisor: Provides personalized suggestions and recommendations for your ML/AI project.
- 📊 Weekly Report: Automatically generates detailed summaries of your weekly works.

|Workflow|Agent|
|:--:|:--:|
|<img width="726" alt="Screenshot 2025-06-18 at 2 54 55 PM" src="https://github.com/user-attachments/assets/2e47310d-97e0-4e12-87ff-4cdbd627a295" />|<img width="728" alt="Screenshot 2025-06-18 at 2 55 04 PM" src="https://github.com/user-attachments/assets/646e98d9-8bf6-45dc-98f8-e025939823b8" />|

## Video Demo

https://github.com/user-attachments/assets/dac7be90-c662-4d0d-8d3a-2bc4df9cffb9

## Milestones

- :rocket: 09/24/2024: Release the `0.4.2` with enhanced `Auto-Kaggle` mode to complete an end-to-end competition with minimal effort.
- :rocket: 09/10/2024: Release the `0.4.0` with new CLIs like `MLE report`, `MLE kaggle`, `MLE integration` and many new
  models like `Mistral`.
- :rocket: 07/25/2024: Release the `0.3.0` with huge refactoring, many integrations, etc. (v0.3.0)
- :rocket: 07/11/2024: Release the `0.2.0` with multiple agents interaction (v0.2.0)
- 👨‍🍼 **07/03/2024: Kaia is born**
- :rocket: 06/01/2024: Release the first rule-based version of MLE agent (v0.1.0)

## Get started

### Installation

#### From PyPI

```bash
# With pip:
pip install -U mle-agent

# With uv:
uv pip install -U mle-agent
```

#### From source

<ol>
<li>Clone the repo

```bash
git clone https://github.com/MLSysOps/MLE-agent.git
cd MLE-agent
```
</li>

<li> Create & activate a virtual env

```bash
uv venv .venv
source .venv/bin/activate      # Linux/macOS
```

<li> Editable install

```bash
pip install -e .               # or: pip install -e .
```

</li>
</ol>

### Usage

```bash
mle new <project name>
```

And a project directory will be created under the current path, you need to start the project under the project
directory.

```bash
cd <project name>
mle start
```

You can also start an interactive chat in the terminal under the project directory:

```bash
mle chat
```

## Use cases

### 🧪 Prototype an ML Baseline

MLE agent can help you prototype an ML baseline with the given requirements, and test the model on the local machine.
The requirements can be vague, such as "I want to predict the stock price based on the historical data".

```bash
cd <project name>
mle start
```

### :bar_chart: Generate Work Report

MLE agent can help you summarize your weekly report, including development progress, communication notes, reference, and
to-do lists.

#### Mode 1: Web Application to Generate Report from GitHub

```bash
cd <project name>
mle report
```

Then, you can visit http://localhost:3000/ to generate your report locally.

#### Mode 2: CLI Tool to Generate Report from Local Git Repository
```bash
cd <project name>
mle report-local --email=<git email> --start-date=YYYY-MM-DD --end-date=YYYY-MM-DD <path_to_git_repo>
```

- `--start-date` and `--end-date` are optional parameters. If omitted, the command will generate a report for the default date range of the last 7 days.
- Replace `<git email>` with your Git email and `<path_to_git_repo>` with the path to your local Git repository.

### :trophy: Start with Kaggle Competition

MLE agent can participate in Kaggle competitions and finish coding and debugging from data preparation to model training
independently. Here is the basic command to start a Kaggle competition:

```bash
cd <project name>
mle kaggle
```

Or you can let the agents finish the Kaggle task without human interaction if you have the dataset and submission file
ready:

```bash
cd <project name>
mle kaggle --auto \
--datasets "<path_to_dataset1>,<path_to_dataset2>,..." \
--description "<description_file_path_or_text>" \
--submission "<submission_file_path>" \
--sub_example "<submission_example_file_path>" \ 
--comp_id "<competition_id>"
```

Please make sure you have joined the competition before running the command. For more details, see the [MLE-Agent Tutorials](https://mle-agent-site.vercel.app/tutorial/Start_a_kaggle_task).

## Roadmap

The following is a list of the tasks we plan to do, welcome to propose something new!

<details>
  <summary><b> :hammer: General Features</b></summary>

- [x] Understand users' requirements to create an end-to-end AI project
- [x] Suggest the SOTA data science solutions by using the web search
- [x] Plan the ML engineering tasks with human interaction
- [x] Execute the code on the local machine/cloud, debug and fix the errors
- [x] Leverage the built-in functions to complete ML engineering tasks
- [x] Interactive chat: A human-in-the-loop mode to help improve the existing ML projects
- [x] Kaggle mode: to finish a Kaggle task without humans
- [x] Summary and reflect the whole ML/AI pipeline
- [ ] Integration with Cloud data and testing and debugging platforms
- [x] Local RAG support to make personal ML/AI coding assistant
- [ ] Function zoo: generate AI/ML functions and save them for future usage

</details>

<details>
  <summary><b>:star: More LLMs and Serving Tools</b></summary>

- [x] Ollama LLama3
- [x] OpenAI GPTs
- [x] Anthropic Claude 3.5 Sonnet

</details>

<details>
  <summary><b>:sparkling_heart: Better user experience</b></summary>

- [x] CLI Application
- [x] Web UI
- [x] Discord

</details>

<details>
  <summary><b>:jigsaw: Functions and Integrations</b></summary>

- [x] Local file system
- [x] Local code exectutor
- [x] Arxiv.org search
- [x] Papers with Code search
- [x] General keyword search
- [ ] Hugging Face
- [ ] SkyPilot cloud deployment
- [ ] Snowflake data
- [ ] AWS S3 data
- [ ] Databricks data catalog
- [ ] Wandb experiment monitoring
- [ ] MLflow management
- [ ] DBT data transform

</details>

## Contributing

We welcome contributions from the community. We are looking for contributors to help us with the following tasks:

- Benchmark and Evaluate the agent
- Add more features to the agent
- Improve the documentation
- Write tests

Please check the [CONTRIBUTING.md](CONTRIBUTING.md) file if you want to contribute.

## Support and Community

- [Discord community](https://discord.gg/SgxBpENGRG). If you have any questions, please ask in the Discord community.

## Citation

```bibtex
@misc{zhang2024mleagent,
title = {MLE-Agent: Your Intelligent Companion for Seamless AI Engineering and Research},
author = {Huaizheng Zhang*, Yizheng Huang*, Lei Zhang},
year = {2024},
note = {\url{https://github.com/MLSysOps/MLE-agent}},
}
```

## License

Check [MIT License](LICENSE) file for more information.
