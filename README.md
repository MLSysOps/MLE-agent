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
<a href="https://discord.gg/SgxBpENGRG"><img src="https://img.shields.io/badge/Discord-Join%20Us-purple?logo=discord&logoColor=white&style=flat" alt="Join our Discord community"></a>

[📚 Docs](https://mle-agent-site.vercel.app/) | 
[🐞 Report Issues](https://github.com/MLSysOps/MLE-agent/issues/new) | 
👋 Join us on <a href="https://discord.gg/SgxBpENGRG" target="_blank">Discord</a>

</div>


## Overview

MLE-Agent is designed as a pairing LLM agent for machine learning engineers and researchers. It is featured by:

- 🤖 Autonomous Baseline Creation: Automatically builds ML/AI baselines.
- 🔍 [Arxiv](https://arxiv.org/) and [Papers with Code](https://paperswithcode.com/) Integration: Access best practices and state-of-the-art methods.
- 🐛 Smart Debugging: Ensures high-quality code through automatic debugger-coder interactions.
- 📂 File System Integration: Organizes your project structure efficiently.
- 🧰 Comprehensive Tools Integration: Includes AI/ML functions and MLOps tools for a seamless workflow.
- ☕ Interactive CLI Chat: Enhances your projects with an easy-to-use chat interface.
- 📊 Weekly Report: Automatically generates detailed summaries of your weekly works.


https://github.com/user-attachments/assets/dac7be90-c662-4d0d-8d3a-2bc4df9cffb9

## Milestones

- :rocket: 09/10/2024: Release the `0.4.0` with new CLIs like `MLE report`, `MLE kaggle`, `MLE integration` and many new models like `Mistral`.
- :rocket: 07/25/2024: Release the `0.3.0` with huge refactoring, many integrations, etc (v0.3.0)
- :rocket: 07/11/2024: Release the `0.2.0` with multiple agents interaction (v0.2.0)
- 👨‍🍼 **07/03/2024: Kaia is born**
- :rocket: 06/01/2024: Release the first rule-based version of MLE agent (v0.1.0)

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

## Use cases

### :bar_chart: Generate Work Report

MLE agent can help you summarize your weekly report, including development progress, communication notes, and to-do lists.

```bash
cd <project name>
mle report
```
Then, you can visit http://localhost:3000/ to generate your report locally.

### :trophy: Start with Kaggle Competition

MLE agent can participate in Kaggle competitions and finish coding and debugging from data preparation to model training independently.
For more details, see the [MLE-Agent Tutorials](https://mle-agent-site.vercel.app/tutorial/Start_a_kaggle_task).

```bash
cd <project name>
mle kaggle
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
  - [x] Kaggle mode: to finish a Kaggle task without humans
  - [ ] Summary and reflect the whole ML/AI pipeline
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

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=MLSysOps/MLE-agent&type=Date)](https://star-history.com/#MLSysOps/MLE-agent&Date)

## License

Check [MIT License](LICENSE) file for more information.
