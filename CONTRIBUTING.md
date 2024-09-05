# Contributing to MLE Agent

This document is a work in progress. If you notice areas for improvement, please feel free to update this guide and submit a pull request!

## Table of Contents

- [Submitting a Pull Request](#submitting-a-pull-request)
- [Ensuring Your Pull Request Gets Accepted](#ensuring-your-pull-request-gets-accepted)
- [The Review Process](#the-review-process)
- [Work in Progress Pull Requests](#work-in-progress-pull-requests)
- [Triaging Issues](#triaging-issues)

## Submitting a Pull Request

To contribute code to MLE Agent, you need to open a [pull request](https://help.github.com/articles/about-pull-requests/). The pull request will be reviewed by the community before it is merged into the core project. Generally, a pull request should be submitted when a unit of work is complete, but you can also share ideas or get feedback through a work in progress (WIP) pull request ([learn more](#work-in-progress-pull-requests)).

1. Familiarize yourself with the project by reading our ["Getting Started Guide"](docs/GETTING_STARTED.md).

2. Follow our [coding standards](docs/CODE_GUIDELINES.md) to ensure consistency across the project.

3. Review our [testing guidelines](docs/TEST_GUIDELINES.md) to understand the project's automated testing framework.

4. [Set up your development environment](docs/DEVELOPMENT_SETUP.md) to make sure you have everything you need to contribute.

5. Make sure you have the latest version of the code by syncing your fork with the main repository:

   ```sh
   git remote add upstream https://github.com/MLSysOps/MLE-agent.git
   git fetch upstream
   git merge upstream/main
   ```

6. Create a branch for the code you will be working on:

   ```sh
   git checkout -b my-new-feature
   ```

7. Write your code, making sure to include tests as needed.

8. Commit your changes with a meaningful commit message:

   ```sh
   git commit -m "Description of the changes"
   ```

9. Push your changes to your fork:

   ```sh
   git push origin my-new-feature
   ```

10. Open a pull request on GitHub. Make sure to include a detailed description of the changes you made and any relevant context.

## Ensuring Your Pull Request Gets Accepted

- Make sure your code follows the coding standards outlined in our code guidelines -- we use [flake8](https://flake8.pycqa.org/en/latest/) to enforce these standards.
- Write tests for any new features or significant changes.
- Ensure all tests pass before submitting your pull request.
- Be responsive to feedback from reviewers.


## The Review Process

Once you submit a pull request, it will be reviewed by the maintainers. They might request changes or provide feedback. The goal is to ensure the code is high quality and aligns with the project's goals.

## Work in Progress Pull Requests

If you want feedback on your work before it's complete, you can open a WIP pull request. This allows you to get input from others on your approach or on specific parts of your code.
When you're ready for a full review, you can mark the pull request as `MRG` for review by removing the `WIP` label.

## Triaging Issues
If you're not ready to submit code but still want to contribute, you can help by triaging issues. This involves confirming bugs, providing additional information, or suggesting ways to reproduce issues.

Thank you for your interest in contributing to MLE Agent!