# Benchmark on MLE-Bench

## Installation

You need to install [Git LFS](https://git-lfs.github.com/) to set up, and your Python version must be >= 3.11.

In Linux/macOS:
```shell
GIT_LFS_SKIP_SMUDGE=1 pip install -e .[bench]
```
In Windows (CMD):
```shell
set GIT_LFS_SKIP_SMUDGE=1
pip install -e .[bench]
```
In Windows (PowerShell):
```
$env:GIT_LFS_SKIP_SMUDGE=1
pip install -e .[bench]
```

Then run the following command to set up the MLE-Bench:
```shell
mle-exp init
```

## Benchmarking (Lite)

### Prepare datasets
MLE-Bench uses the Kaggle API to download the raw datasets. 
Ensure your Kaggle credentials (kaggle.json) is in the `~/.kaggle/` folder 
(default location).  
The dataset will be downloaded to the system default cache directory.

Prepare the lite dataset ([15 smaller datasets](https://github.com/openai/mle-bench?tab=readme-ov-file#lite-evaluation)):
```shell
# Prepare lite dataset (smaller version of the dataset)
mle-exp prepare --lite
```
Alternatively, you can prepare the dataset for a specific competition:
```shell
mle-exp prepare -c <competition-id>
```
### Run MLE Agent (WIP)
```shell
mle kaggle <competition-id>
```

### Grade submission
```shell
mle-exp grade-sample <PATH_TO_SUBMISSION> <competition-id>
```

## Benchmarking (Full)

### Prepare full 75 datasets
```shell
mle-exp prepare --all
```
### Run MLE Agent (WIP)
```shell
mle kaggle <competition-id>
```

### Grade submission
```shell
mle-exp grade-sample <PATH_TO_SUBMISSION> <competition-id>
```
