<div align="center">
<img alt="keia-llama" height="200px" src="assets/keia_llama.webp">
<h1 align="center">Keia: A Pair Agent for Machine Learning Engineer</h1>
<p align="center">:love_letter: Fathers' love for Keia :love_letter:</p>

![GitHub commit activity](https://img.shields.io/github/commit-activity/w/MLSysOps/MLE-agent)
![GitHub contributors from allcontributors.org](https://img.shields.io/github/all-contributors/MLSysOps/MLE-agent)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/MLSysOps/MLE-agent/total)
![PyPI - Downloads](https://img.shields.io/pypi/dm/mle-agent)
![GitHub License](https://img.shields.io/github/license/MLSysOps/MLE-agent)


<a href="https://discord.gg/SgxBpENGRG"><img src="https://img.shields.io/badge/Discord-Join%20Us-purple?logo=discord&logoColor=white&style=flat" alt="Join our Discord community"></a>
![X (formerly Twitter) Follow](https://img.shields.io/twitter/follow/MLE_Agent?logoColor=black)
</div>




Keia is an MLE agent that helps you to plan, execute, and optimize your AI projects.

## Installation

```bash
pip install -e .
```

## Usage

You need to set an OpenAI API key before running the agent. You can use the CLI to set the key:

```bash
mle config
```

If you want to use aws to launch mle jobs, we recommend you also set up your aws and [[skypilot]](https://skypilot.readthedocs.io/en/latest/getting-started/installation.html) by

```bash
pip install "skypilot-nightly[aws]"
aws configure
sky check aws
```

### Quick start

```bash
mle new test-project

mle start
```


## License

Check [LICENSE](LICENSE) file for more information.
