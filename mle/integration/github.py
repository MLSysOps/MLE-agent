import os
import base64
import requests
from datetime import datetime, timezone
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
        """
        Make a GET request to the GitHub API.
        :param endpoint: The endpoint to request.
        :param params: The parameters to include in the request.
        :return: The JSON response from the request.
        """
        url = f"{self.BASE_URL}/repos/{self.github_repo}/{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def _process_items(self, endpoint, start_date=None, end_date=None, username=None, limit=None):
        """
        Helper method to process issues or pull requests.
        :param endpoint: The endpoint to process (e.g., 'issues' or 'pulls')
        :param start_date: Start date for issue/PR range (inclusive), in 'YYYY-MM-DD' format
        :param end_date: End date for issue/PR range (inclusive), in 'YYYY-MM-DD' format
        :param username: GitHub username to filter issues/PRs (optional)
        :param limit: Maximum number of issues/PRs to retrieve (default is None, which retrieves all in range)
        :return: Dictionary of issues and pull requests
        """
        params = {
            "state": "all",
            "per_page": 100,  # GitHub API max per page
            "sort": "created",
            "direction": "desc"
        }
        if username:
            params["creator"] = username
        if start_date:
            params["since"] = f"{start_date}T00:00:00Z"

        items = {}
        page = 1
        while True:
            params["page"] = page
            page_items = self._make_request(endpoint, params=params)
            if not page_items:
                break

            for item in page_items:
                created_at = datetime.strptime(item['created_at'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

                if end_date and created_at > datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59,
                                                                                             second=59,
                                                                                             tzinfo=timezone.utc):
                    continue
                if start_date and created_at < datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc):
                    return items  # Stop if we've passed the start date

                items[item['number']] = {
                    "number": item['number'],
                    "title": item['title'],
                    "state": item['state'],
                    "created_at": item['created_at'],
                    "author": item['user']['login'],
                    "body": item['body']
                }

                if limit and len(items) >= limit:
                    return items

            page += 1

        return items

    def get_source_code(self, file_pattern="*"):
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

    def get_commit_history(self, start_date=None, end_date=None, username=None, limit=None):
        """
        Process commit history within a specified date range and for a specific user.
        :param start_date: Start date for commit range (inclusive), in 'YYYY-MM-DD' format
        :param end_date: End date for commit range (inclusive), in 'YYYY-MM-DD' format
        :param username: GitHub username to filter commits (optional)
        :param limit: Maximum number of commits to retrieve (default is None, which retrieves all commits in range)
        :return: Dictionary of commits
        """
        params = {"per_page": 100}  # GitHub API max per page
        if start_date:
            params["since"] = f"{start_date}T00:00:00Z"
        if end_date:
            params["until"] = f"{end_date}T23:59:59Z"
        if username:
            params["author"] = username

        commits = []
        page = 1
        while True:
            params["page"] = page
            page_commits = self._make_request("commits", params=params)
            if not page_commits:
                break
            commits.extend(page_commits)
            if limit and len(commits) >= limit:
                commits = commits[:limit]
                break
            page += 1

        commit_history = {}
        for commit in commits:
            commit_date = datetime.strptime(commit['commit']['author']['date'], "%Y-%m-%dT%H:%M:%SZ")
            commit_date = commit_date.replace(tzinfo=timezone.utc)

            if (not start_date or commit_date >= datetime.strptime(start_date, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc)) and \
                    (not end_date or commit_date <= datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59,
                                                                                                    second=59,
                                                                                                    tzinfo=timezone.utc)) and \
                    (not username or commit['author']['login'] == username):
                commit_history[commit['sha']] = {
                    "author": commit['commit']['author']['name'],
                    "username": commit['author']['login'] if commit['author'] else None,
                    "date": commit['commit']['author']['date'],
                    "message": commit['commit']['message']
                }

        return commit_history

    def get_issues(self, start_date=None, end_date=None, username=None, limit=None):
        """
        Process issues within a specified date range and for a specific user.
        :param start_date: Start date for issue range (inclusive), in 'YYYY-MM-DD' format
        :param end_date: End date for issue range (inclusive), in 'YYYY-MM-DD' format
        :param username: GitHub username to filter issues (optional)
        :param limit: Maximum number of issues to retrieve (default is None, which retrieves all in range)
        :return: Dictionary of issues
        """
        return self._process_items("issues", start_date, end_date, username, limit)

    def get_pull_requests(self, start_date=None, end_date=None, username=None, limit=None):
        """
        Process pull requests within a specified date range and for a specific user.
        :param start_date: Start date for PR range (inclusive), in 'YYYY-MM-DD' format
        :param end_date: End date for PR range (inclusive), in 'YYYY-MM-DD' format
        :param username: GitHub username to filter PRs (optional)
        :param limit: Maximum number of PRs to retrieve (default is None, which retrieves all in range)
        :return: Dictionary of pull requests
        """
        return self._process_items("pulls", start_date, end_date, username, limit)

    def get_pull_request_diff(self, pr_number):
        """
        Get the git commit diff of a specific pull request.
        :param pr_number: The number of the pull request.
        :return: A string containing the diff content of the pull request.
        """
        try:
            response = self._make_request(f"pulls/{pr_number}")
            return response
        except requests.exceptions.RequestException as e:
            error_message = f"Error fetching PR #{pr_number} diff: {str(e)}"
            if e.response is not None:
                error_message += f" (Status code: {e.response.status_code})"
            print(error_message)
            return f"Unable to fetch diff: {error_message}"


if __name__ == '__main__':
    # Example usage of the GithubInte class
    github = GithubInte("huangyz0918/termax")
    print(github.get_pull_requests(limit=10, username='SilinMeng0510'))
