<div align="center">
<h1 align="center">Kaia: A Pair Agent for AI Engineer / Researchers</h1>
<p align="center">:love_letter: Fathers' love for Kaia :love_letter:</p>
<img alt="kaia-llama" height="200px" src="assets/kaia_llama.webp">

![](https://github.com/MLSysOps/MLE-agent/actions/workflows/lint.yml/badge.svg) 
![](https://github.com/MLSysOps/MLE-agent/actions/workflows/test.yml/badge.svg) 
![GitHub commit activity](https://img.shields.io/github/commit-activity/w/MLSysOps/MLE-agent)
![PyPI - Downloads](https://img.shields.io/pypi/dm/mle-agent)
[![Downloads](https://static.pepy.tech/badge/mle-agent)](https://pepy.tech/project/mle-agent)
![GitHub License](https://img.shields.io/github/license/MLSysOps/MLE-agent)


<a href="https://discord.gg/SgxBpENGRG"><img src="https://img.shields.io/badge/Discord-Join%20Us-purple?logo=discord&logoColor=white&style=flat" alt="Join our Discord community"></a>
![X (formerly Twitter) Follow](https://img.shields.io/twitter/follow/MLE_Agent?logoColor=black)

https://github.com/MLSysOps/MLE-agent/assets/5894780/e3c1ad52-3e3e-4d57-a661-d927f2e3a775

</div>



## Overview

MLE-Agent is designed as a pairing LLM agent for machine learning engineers and researchers. It is featured in two major modes:

- :rocket: **Kaggle Mode** will help you to easily participate in Kaggle competitions, prepare submissions and get a good score.
- :coffee: **Baseline Mode** can quickly build a baseline model for your AI project according to your requirements.
- :fire: **Advanced Mode (Coming Soon)** is designed to utilize users' favorite MLOps tools, understand SOTA methods, and suggest optimizations for users' machine learning projects.


## Milestones

:rocket: June 16th, 2024: Pre-release the **Kaggle Mode** (need to install from the source code)

:rocket: June 1st, 2024: Release the **Baseline Mode** (v0.1.0)

## Get started

### Installation

```bash
pip install mle-agent
```

### Configuration

You must set up an LLM and choose tools before using the agent.
```bash
mle config
```

### Usage (Baseline Mode)

**Create a new project**
```bash
mle new <project name>
```

A workspace with `<project name>` will be created where you execute the `mle new` command.

**Start a project**

```bash
mle start
```


> [!NOTE]
> 
> - Debugging on the cloud may incur high costs, please ensure you have enough budget.
> - You can start a project under any path, the code/data generated will be stored in the target workspace.


**Project-related operations**

```bash
mle project ls # show all the available projects
mle project delete <project name> # delete a given project
mle project switch # switch the current working project
mle project show # show the status of the current project
```

## Roadmap

The following is a list of the tasks we plan to do, welcome to propose something new!

<details>
  <summary><b> :hammer: Plan, Generate, Execute and Debug Code</b></summary>
  
  - [x] An easy-to-use CLI interface
  - [x] Create/Select/Delete a project
  - [x] Understand users' requirements to suggest the file name, dataset, task, model arch, etc
  - [x] Generate a detailed coding plan
  - [x] Write baseline model code
  - [x] Execute the code on the local machine/cloud
  - [x] Debug the code and revise the code
  - [x] Googling the error message to debug the code
  - [ ] Data Augmentation
  - [ ] Hyperparameter tuning
  - [ ] Model evaluation

</details>

<details>
  <summary><b>:star: More LLMs and Serving Tools</b></summary>
  
  - [x] Ollama LLama 2/3
  - [x] OpenAI GPT-3.5
  - [x] OpenAI GPT-4
  - [ ] Codellama
  - [ ] Codemitral
</details>

<details>
  <summary><b>:sparkling_heart: Better user experience</b></summary>
  
  - [ ] Web UI (coming soon)
  - [ ] Discord
</details>

<details>
  <summary><b>:jigsaw: Integrations</b></summary>

  - [x] SkyPilot
  - [ ] Snowflake/Databricks 
  - [ ] W&B/MLflow 
  - [ ] DBT/Airflow
  - [ ] HuggingFace
  - [ ] Paper with Code
  - [ ] Arxiv
</details>

## Contributing

We welcome contributions from the community. We are looking for contributors to help us with the following tasks:

- Benchmark and Evaluate the agent
- Add more features to the agent
- Improve the documentation
- Write tests

If you are interested in contributing, please check the [CONTRIBUTING.md](CONTRIBUTING.md) file.

## Support and Community

- [Discord community](https://discord.gg/SgxBpENGRG). If you have any questions, please feel free to ask in the Discord community.
- [Twitter](https://twitter.com/MLE_Agent). Follow us on Twitter to get the latest updates.


## License

Check [LICENSE](LICENSE) file for more information.
