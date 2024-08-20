import os
import base64
import numpy as np
from github import Github


class GithubInte:

    def __init__(self, github_repo: str, github_token=None):
        """
        Initialize the GithubInte class with a Github token.
        :param github_repo: the Github repository to process, in the format of <owner>/<repo>.
        :param github_token: the Github token.
        """
        if not github_token:
            github_token = os.getenv("GITHUB_TOKEN")
        self.github = Github(github_token)
        self.repo = self.github.get_repo(github_repo)

    def process_source_code(self):
        contents = self.repo.get_contents("")
        source_code = {}
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(self.repo.get_contents(file_content.path))
            else:
                try:
                    if file_content.encoding == 'base64':
                        file_text = base64.b64decode(file_content.content).decode('utf-8')
                    else:
                        file_text = file_content.decoded_content.decode('utf-8')
                    source_code[file_content.path] = file_text
                except Exception as e:
                    print(f"Error processing file {file_content.path}: {str(e)}")
                    source_code[file_content.path] = "Unable to process content"
        return source_code

    def process_commit_history(self, limit=10):
        commits = self.repo.get_commits()
        commit_history = {}
        for i, commit in enumerate(commits[:limit]):
            commit_history[commit.sha] = {
                "author": commit.commit.author.name,
                "date": commit.commit.author.date.isoformat(),
                "message": commit.commit.message
            }
        return commit_history

    def process_issues_and_prs(self, limit=10):
        issues = self.repo.get_issues(state="all")
        prs = self.repo.get_pulls(state="all")
        issues_prs = {}
        for item in list(issues)[:limit] + list(prs)[:limit]:
            item_type = 'Issue' if hasattr(item, 'issue') else 'PR'
            issues_prs[f"{item_type}-{item.number}"] = {
                "type": item_type,
                "number": item.number,
                "title": item.title,
                "state": item.state,
                "created": item.created_at.isoformat(),
                "author": item.user.login,
                "body": item.body[:200] + "..." if item.body else ""
            }
        return issues_prs
