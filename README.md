# MLE-agent

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