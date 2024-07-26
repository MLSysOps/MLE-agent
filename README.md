<div align="center">
<h1 align="center">MLE-Agent: Your intelligent companion for seamless AI engineering and research.</h1>
<img alt="kaia-llama" height="200px" src="assets/kaia_llama.webp">
<p align="center">:love_letter: Fathers' love for Kaia :love_letter:</p>

![](https://github.com/MLSysOps/MLE-agent/actions/workflows/lint.yml/badge.svg) 
![](https://github.com/MLSysOps/MLE-agent/actions/workflows/test.yml/badge.svg) 
![PyPI - Version](https://img.shields.io/pypi/v/mle-agent)
[![Downloads](https://static.pepy.tech/badge/mle-agent)](https://pepy.tech/project/mle-agent)
![GitHub License](https://img.shields.io/github/license/MLSysOps/MLE-agent)
<a href="https://discord.gg/SgxBpENGRG"><img src="https://img.shields.io/badge/Discord-Join%20Us-purple?logo=discord&logoColor=white&style=flat" alt="Join our Discord community"></a>

</div>


## Overview

MLE-Agent is designed as a pairing LLM agent for machine learning engineers and researchers. It is featured by:

- 🤖 Autonomous Baseline Creation: Automatically builds ML/AI baselines.
- 🔍 [Arxiv](https://arxiv.org/) and [Papers with Code](https://paperswithcode.com/) Integration: Access best practices and state-of-the-art methods.
- 🐛 Smart Debugging: Ensures high-quality code through automatic debugger-coder interactions.
- 📂 File System Integration: Organizes your project structure efficiently.
- 🧰 Comprehensive Tools Integration: Includes AI/ML functions and MLOps tools for a seamless workflow.
- ☕ Interactive CLI Chat: Enhances your projects with an easy-to-use chat interface.


https://github.com/user-attachments/assets/dac7be90-c662-4d0d-8d3a-2bc4df9cffb9

## Milestones

- :rocket: 25 July 2024: Release the `0.3.0` with huge refactoring, many integrations, etc (v0.3.0)
- :rocket: 11 July 2024: Release the `0.2.0` with multiple agents interaction (v0.2.0)
- :rocket: June 1st, 2024: Release the first rule-based version of MLE agent (v0.1.0)

## Get started

### Installation

```bash
pip install mle-agent -U
# or from source
git clone git@github.com:MLSysOps/MLE-agent.git
pip install -e .
```

### Usage

```bash
mle new <project name>
```

And a project directory will be created under the current path, you need to start the project under the project directory.

```bash
cd <project name>
mle start
```

You can also start an interactive chat in the terminal under the project directory:

```bash
mle chat
```

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
  - [ ] Kaggle mode: to finish a Kaggle task without humans
  - [ ] Summary and reflect the whole ML/AI pipeline
  - [ ] Integration with Cloud data and testing and debugging platforms
  - [ ] Local RAG support to make personal ML/AI coding assistant
  - [ ] Function zoo: generate AI/ML functions and save them for future usage


</details>

<details>
  <summary><b>:star: More LLMs and Serving Tools</b></summary>
  
  - [x] Ollama LLama3
  - [x] OpenAI GPTs
  - [ ] Anthropic Claude 3.5 Sonnet
</details>

<details>
  <summary><b>:sparkling_heart: Better user experience</b></summary>

  - [x] CLI Application
  - [ ] Web UI
  - [ ] Discord
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
