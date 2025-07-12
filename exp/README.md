# Benchmark on MLE-Bench

## Installation

You need to install [Git LFS](https://git-lfs.github.com/) to set up, and your Python version must be >= 3.11.

```shell
GIT_LFS_SKIP_SMUDGE=1 pip install -e .[bench]

# In Windows CMD
set GIT_LFS_SKIP_SMUDGE=1
pip install -e .[bench]

# In Windows PowerShell
$env:GIT_LFS_SKIP_SMUDGE=1
pip install -e .[bench]
```

Then run the following command to set up the MLE-Bench:
```shell
mle-exp init
```

## Usage

- Prepare the dataset:
```shell
# Prepare all dataset
mle-exp prepare --all

# Prepare lite dataset (smaller version of the dataset)
mle-exp prepare --lite

# Prepare a specific dataset
mle-exp prepare -c <competition-id>
```

- Grade individual submissions
```shell
mle-exp grade-sample <PATH_TO_SUBMISSION> <competition-id>
```

More commands can be checked using:
```shell
mle-exp --help
```