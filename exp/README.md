# Benchmark on MLE-Bench

## Installation

Requirements:
You need to have [Git LFS](https://git-lfs.github.com/) installed to clone the repository.

```shell
set GIT_LFS_SKIP_SMUDGE=1
pip install -e .[bench]
```

Then run the following command to set up the MLE-Bench:
```shell
python ./install.py
```

## Usage

- Prepare the dataset:
```shell
# Prepare all dataset
python ./cli.py bench prepare --all

# Prepare lite dataset (smaller version of the dataset)
python ./cli.py bench prepare --lite

# Prepare a specific dataset
python ./cli.py bench prepare -c <competition-id>
```

- Grade individual submissions
```shell
python ./cli.py bench grade-sample <PATH_TO_SUBMISSION> spaceship-titanic
```

More commands can be check use:
```shell
python ./cli.py bench --help
```