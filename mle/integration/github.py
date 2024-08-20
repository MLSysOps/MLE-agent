import os
import base64
import requests
from datetime import datetime
from fnmatch import fnmatch


class GithubInte:
    BASE_URL = "https://api.github.com"

    def __init__(self, github_repo: str, github_token=None):
        """
        Initialize the GithubInte class with a Github token.
        :param github_repo: the Github repository to process, in the format of <owner>/<repo>.
        :param github_token: the Github token.
        """
        self.github_repo = github_repo
        if not github_token:
            github_token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def _make_request(self, endpoint, params=None):
        """Make a GET request to the GitHub API."""
        url = f"{self.BASE_URL}/repos/{self.github_repo}/{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def process_source_code(self, file_pattern="*"):
        """
        Process source code files in the repository.
        :param file_pattern: Wildcard pattern to filter files (e.g., "*.py" for Python files)
        :return: Dictionary with file paths as keys and file contents as values
        """

        def get_contents(path=""):
            contents = self._make_request(f"contents/{path}")
            if isinstance(contents, list):
                for item in contents:
                    if item['type'] == 'dir':
                        yield from get_contents(item['path'])
                    elif fnmatch(item['name'], file_pattern):
                        yield item
            elif fnmatch(contents['name'], file_pattern):
                yield contents

        source_code = {}
        for item in get_contents():
            try:
                if 'content' in item and item.get('encoding') == 'base64':
                    content = base64.b64decode(item['content']).decode('utf-8')
                elif 'download_url' in item:
                    response = requests.get(item['download_url'], headers=self.headers)
                    response.raise_for_status()
                    content = response.text
                else:
                    content = f"File too large to process directly. Size: {item.get('size', 'unknown')} bytes"
                source_code[item['path']] = content
            except Exception as e:
                error_message = f"Error: {str(e)}"
                if isinstance(e, requests.exceptions.RequestException):
                    error_message += f" (Status code: {e.response.status_code})"
                print(f"Error processing file {item['path']}: {error_message}")
                source_code[item['path']] = f"Unable to process content: {error_message}"
        return source_code

    def process_commit_history(self, limit=10):
        commits = self._make_request("commits", params={"per_page": limit})
        commit_history = {}
        for commit in commits:
            commit_history[commit['sha']] = {
                "author": commit['commit']['author']['name'],
                "date": commit['commit']['author']['date'],
                "message": commit['commit']['message']
            }
        return commit_history

    def process_issues_and_prs(self, limit=10):
        issues = self._make_request("issues", params={"state": "all", "per_page": limit})
        prs = self._make_request("pulls", params={"state": "all", "per_page": limit})
        issues_prs = {}

        for item in issues + prs:
            item_type = 'PR' if 'pull_request' in item else 'Issue'
            issues_prs[f"{item_type}-{item['number']}"] = {
                "type": item_type,
                "number": item['number'],
                "title": item['title'],
                "state": item['state'],
                "created": item['created_at'],
                "author": item['user']['login'],
                "body": (item['body'][:200] + "...") if item['body'] else ""
            }
        return issues_prs
