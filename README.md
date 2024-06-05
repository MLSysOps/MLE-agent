<div align="center">
<h1 align="center">Keia: A Pair Agent for AI Engineer / Researchers</h1>
<p align="center">:love_letter: Fathers' love for Keia :love_letter:</p>
<img alt="keia-llama" height="200px" src="assets/keia_llama.webp">

![](https://github.com/MLSysOps/MLE-agent/actions/workflows/lint.yml/badge.svg) 
![](https://github.com/MLSysOps/MLE-agent/actions/workflows/test.yml/badge.svg) 
![GitHub commit activity](https://img.shields.io/github/commit-activity/w/MLSysOps/MLE-agent)
![PyPI - Downloads](https://img.shields.io/pypi/dm/mle-agent)
![GitHub License](https://img.shields.io/github/license/MLSysOps/MLE-agent)


<a href="https://discord.gg/SgxBpENGRG"><img src="https://img.shields.io/badge/Discord-Join%20Us-purple?logo=discord&logoColor=white&style=flat" alt="Join our Discord community"></a>
![X (formerly Twitter) Follow](https://img.shields.io/twitter/follow/MLE_Agent?logoColor=black)


</div>




## Overview
_**The project is under active development. The API may change frequently.**_

MLE-Agent is designed as a pairing LLM agent for machine learning engineers and researchers. It is featured in two major modes:

- :coffee: **Baseline Mode** is designed to quickly build a baseline model for your AI project.
- :fire: **Advanced Mode (Coming Soon)** is designed to utilize users' favorite MLOps tools, understand SOTA methods, and suggest optimizations for users' machine learning projects.




## Milestones

:rocket: June 1st, 2024: Release the **Baseline Mode** (v0.1.0)

## Get started

### Installation

install from pypi
```bash
pip install mle-agent
```

### Configuration

You need to set up an LLM and choose tools before using the agent.
```bash
mle config
```

### Usage (Baseline Mode)

Create a new project
```bash
mle new <project name>
```

A workspace with `<project name>` will be created where you execute the `new` command.

Start a project

**_Debugging on  cloud may occur high cost, please make sure you have enough budget._**
```bash
mle start
```

You can start a project under any path, the code/data generated will be stored in the target workspace.

Other operations.
```bash
mle project ls # show all the available projects
mle project delete <project name> # delete a given project
mle project switch # switch the current working project
```

## Roadmap

The following is a list of features that we plan to implement in the future. The list is not exhaustive, and we may add more features as we go along.

### Plan, Generate, Execute and Debug Code

- [x] An easy-to-use CLI interface
- [x] Create/Select/Delete a project
- [x] Understand users' requirements to suggest the file name, dataset, task, model arch, etc
- [x] Generate a detailed coding plan
- [x] Write baseline model code
- [x] Execute the code on the local machine / cloud
- [x] Debug the code and revise the code
- [x] Googling the error message to debug the code
- [ ] Data Augmentation
- [ ] Hyperparameter tuning
- [ ] Model evaluation

### More LLMs and Serving tools

- [x] Ollama
- [x] GPT-3.5
- [ ] GPT-4
- [ ] Codellama
- [ ] Codemitral

### Better user experience

- [ ] web interface (coming soon)
- [ ] discord bot

### Integrate with AI/ML Tools

- [ ] snowflake / databricks 
- [ ] wandb / mlflow 
- [x] skypilot
- [ ] dbt / airflow

### Integrate with research tools

- [ ] huggingface
- [ ] paper with code
- [ ] arxiv

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
