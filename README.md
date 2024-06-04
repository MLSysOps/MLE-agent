<div align="center">
<h1 align="center">Keia: A Pair Agent for AI Engineer / Researchers</h1>
<p align="center">:love_letter: Fathers' love for Keia :love_letter:</p>
<img alt="keia-llama" height="200px" src="assets/keia_llama.webp">

![GitHub commit activity](https://img.shields.io/github/commit-activity/w/MLSysOps/MLE-agent)
![GitHub contributors from allcontributors.org](https://img.shields.io/github/all-contributors/MLSysOps/MLE-agent)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/MLSysOps/MLE-agent/total)
![PyPI - Downloads](https://img.shields.io/pypi/dm/mle-agent)
![GitHub License](https://img.shields.io/github/license/MLSysOps/MLE-agent)


<a href="https://discord.gg/SgxBpENGRG"><img src="https://img.shields.io/badge/Discord-Join%20Us-purple?logo=discord&logoColor=white&style=flat" alt="Join our Discord community"></a>
![X (formerly Twitter) Follow](https://img.shields.io/twitter/follow/MLE_Agent?logoColor=black)
</div>


## Overview
_The project is under active development. The API may change frequently._

**Keia (MLE-Agent)** is designed to be a pair agent for machine learning engineers or researchers. It includes two modes: **Baseline Mode** and **Advanced Mode**. 

:coffee: **Baseline Mode** is designed to quickly build a baseline model for users' projects.

:fire: **Advanced Mode (Coming Soon)** is designed to utilize users' favorite MLOps tools, understand SOTA methods, and suggest optimizations for users' machine learning projects.




## Milestones

:rocket: June 1st, 2024: Release the **Baseline Mode** (v0.1.0)

## Get started

### Installation

install from pypi
```bash
pip install mle-agent
```

install from source
```bash
git clone git@github.com:MLSysOps/MLE-agent.git
pip install .
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

Start a project
```bash
mle start
```

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

## Acknowledgements

We would like to thank the following contributors for their help with the project:


## License

Check [LICENSE](LICENSE) file for more information.
