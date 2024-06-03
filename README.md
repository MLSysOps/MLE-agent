<div align="center">
<h1 align="center">Keia: A Pair Agent for Machine Learning Engineer / Researchers</h1>
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

**Baseline Mode** is designed to quickly build a baseline model for users' projects.

**Advanced Mode (Coming Soon)** is designed to utilize users' favorite MLOps tools and new methods, and suggest optimizations for users' machine learning projects.




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
pip install -e .
```

### Configuration

You need to set up an LLM and choose tools before using the agent.
```bash
mle config
```

### Usage (Baseline Mode)

Create a new project
```bash
mle new test-project
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

### Baseline Mode

- [x] An easy-to-use CLI interface
- [x] Create/Select/Delete a project
- [x] Understand users' requirements to suggest the file name, dataset, task, model arch, etc
- [x] Generate a detailed coding plan
- [x] Write baseline model code
- [x] Execute the code on the local machine
- [x] Execute the code on the cloud
- [x] Debug the code and revise the code
- [x] Googling the error message to debug the code


### Advanced Mode (Coming Soon)



## License

Check [LICENSE](LICENSE) file for more information.
