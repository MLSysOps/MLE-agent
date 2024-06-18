import os
import re
import ast

from .base import BaseAgent
from agent.integration.github import (
    retrieve_repos,
    retrieve_repo_contents,
    retrieve_file_content,
)

TOKEN = os.getenv("TOKEN", "")


class CodeRetrieveAgent(BaseAgent):

    def system_pmpt_retrival_keywords(self) -> str:
        return f"""
        As an assistant to an ML Engineer, you need to generate 5 keywords based on the
        user's project and requirements description. These keywords will be used to search
        for the relevant tools, examples, or benchmarks from GitHub.

        The output format should be:
        ["keyword-1", "keyword-2", "keyword-3"]
        """

    def system_pmpt_retrival_repos(self) -> str:
        return f"""
        You are an ML Engineer assistant. You need to find three repositories related to
        the provided GitHub repos. These repositories might contain useful examples or usage
        cases for frameworks. You need to identify the three most useful repositories for
        the project.

        Some preferred repositories:
        1. Popular (more stars/forks) repositories contain many solid examples.
        2. Official repositories contain latest examples and cases.

        Output format should be raw JSON, for example:
        ```json
        [{{"name": "pytorch/pytorch", "license": "...", ...}}, ...]
        ```
        """

    def system_pmpt_retrival_codes(self) -> str:
        return f"""
        As an ML Engineer assistant, you need to help users find the three most relevant code
        directories or code files from the given repository for their projects and requirements.

        1. Some valuable content in the code repository may be under certain directories, such
           as `examples/.../xxx.py`, `benchmarks/.../xxx.py`, and you may choose them.
        2. The code files in some certain directories, such as `examples/xxx.py` can be valuale
           for user's projects and requirements.
        3. Do not select any configs, try to select the code or example files.
        4. All your picked up files or directories should be unique.
        5. Your picked files must in the given repository lists.

        Output format should be raw JSON, for example:
        ```json
        [{{"path": "...", "type": "...", "size": ...}}, ...]
        ```
        """

    def project_prompt(self) -> str:
        return f"""
        User's project: {self.project.name}
        User's requirements: {self.project.requirement}
        Description of the project: {self.project.description}
        Project language: {self.project.lang}
        """

    def gen_keywords(self) -> list[str]:
        chat_history = [
            {"role": 'system', "content": self.system_pmpt_retrival_keywords()},
            {"role": 'user', "content": self.project_prompt()}
        ]
        return ast.literal_eval(self.model.query(chat_history))

    def retrieve_repos(self, all_repos) -> list[dict]:
        chat_history = [
            {"role": 'system', "content": self.system_pmpt_retrival_repos()},
            {"role": 'user', "content": self.project_prompt()},
            {"role": 'user', "content": f"github repository lists: {all_repos}"}
        ]
        match = re.search(r"```json([^`]*)```", self.model.query(chat_history), re.DOTALL)
        if match:
            return ast.literal_eval(match.group(1).strip())
        return None

    def retrieve_codes(self, repo, paths) -> list[dict]:
        paths = [
            {
                "path": path["path"],
                "type": path["type"],
                "size": path["size"]
            } for path in paths
        ]

        chat_history = [
            {"role": 'system', "content": self.system_pmpt_retrival_codes()},
            {"role": 'user', "content": self.project_prompt()},
            {"role": 'user', "content": f"github repository: {repo}"},
            {"role": 'user', "content": f"repository files: {paths}"},
        ]
        output = self.model.query(chat_history)
        match = re.search(r"```json([^`]*)```", output, re.DOTALL)
        if match:
            return ast.literal_eval(match.group(1).strip())
        return None

    def invoke(self):
        """
        Invoke the agent.
        """
        # step 1: find relevant github repos
        relevant_repos = []
        for kw in self.gen_keywords():
            repos = retrieve_repos(kw, self.project.lang, TOKEN)
            relevant_repos.extend([
                {
                "name": repo["full_name"],
                "description": repo["description"],
                "forks": repo["forks_count"],
                "stars": repo["stargazers_count"],
                "license": repo["license"].get("name", "") if repo.get("license") else "",
            } for repo in repos[:5]])
        relevant_repos = self.retrieve_repos(relevant_repos)

        # step 2: select the matched codes
        relevant_codes = []
        for repo in relevant_repos:
            # it currently let agent to glance code / dir to select matched codes
            # TODO: support reflect chain and RAG to match codes
            owner, repo_name = repo["name"].split('/')
            paths = retrieve_repo_contents(owner, repo_name, "/", TOKEN)

            def glance_retrieve_codes():
                output = self.retrieve_codes(repo, paths)
                for o in output:
                    if not o["type"] == "dir":
                        continue
                    paths.extend(retrieve_repo_contents(owner, repo_name, o["path"], TOKEN) or [])
                return output

            retry_chanices = 5
            output = glance_retrieve_codes()
            while not all([o["type"] == "file" for o in output]):
                retry_chanices -= 1
                output = glance_retrieve_codes()
                if retry_chanices <= 0:
                    break

            relevant_codes.extend([
                {
                    "repo": repo["name"],
                    "path": o["path"],
                    "content": retrieve_file_content(owner, repo_name, o["path"], TOKEN),
                } for o in output if o["type"] == "file"])

        return relevant_codes