import os
import base64
import requests
import questionary
from fnmatch import fnmatch
from datetime import datetime, timezone, timedelta


def github_login():
    """
    GitHub login by API token.
    :returns: API key.
    """
    token = questionary.password(
        "What is your GitHub token? (https://github.com/settings/tokens)").ask()
    return token


class GitHubIntegration:
    BASE_URL = "https://api.github.com"

    def __init__(self, github_repo: str, github_token=None):
        """
        Initialize the GithubIntegration class with a Github token.
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

    def _make_request(self, endpoint=None, params=None):
        """
        Make a GET request to the GitHub API.
        :param endpoint: The endpoint to request.
        :param params: The parameters to include in the request.
        :return: The JSON response from the request.
        """
        url = f"{self.BASE_URL}/repos/{self.github_repo}" + (f"/{endpoint}" if endpoint else "")
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

    def get_user_info(self):
        """
        Get user information by the given token.
        :return: The user information dictionary
        """
        response = requests.get(f"{self.BASE_URL}/user", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_readme(self):
        """
        Get readme content of the repository.
        :return: The readme content
        """
        content = self.get_source_code("README.md")
        if len(content):
            return list(content.values())[0]
        return None

    def get_license(self):
        """
        Get license of the repository.
        :return: The license
        """
        metadata = self._make_request().get("license", {})
        return {
            "name": metadata.get("name"),
            "url": metadata.get("url"),
        }

    def get_contributors(self):
        """
        Get the contributors of the repository.
        :return: The list of the contributors' information
        """
        return [
            {
                "user": contributor["login"],
                "avatar": contributor["avatar_url"],
                "contributions": contributor["contributions"],
            }
            for contributor in self._make_request("contributors")
        ]

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

    def get_issues(
            self,
            start_date=None,
            end_date=None,
            username=None,
            limit=None,
            detailed=True,
            open_only=False
    ):
        """
        Process issues (excluding pull requests) within a specified date range and for a specific user.
        :param start_date: Start date for issue range (inclusive), in 'YYYY-MM-DD' format
        :param end_date: End date for issue range (inclusive), in 'YYYY-MM-DD' format
        :param username: GitHub username to filter issues (optional)
        :param limit: Maximum number of issues to retrieve (default is None, which retrieves all in range)
        :param detailed: If True, return full issue details. If False, return only title, date, and opener's username
        :param open_only: If True, only return open issues
        :return: List of issues (detailed or simplified based on the 'detailed' parameter)
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

        issues = []
        page = 1
        while True:
            params["page"] = page
            page_items = self._make_request("issues", params=params)
            if not page_items:
                break

            for item in page_items:
                # Skip pull requests
                if 'pull_request' in item:
                    continue

                created_at = datetime.strptime(item['created_at'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

                if end_date and created_at > datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59,
                                                                                             second=59,
                                                                                             tzinfo=timezone.utc):
                    continue
                if start_date and created_at < datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc):
                    return issues  # Stop if we've passed the start date

                if open_only and item['state'] != 'open':
                    continue

                if detailed:
                    issue = {
                        "number": item['number'],
                        "title": item['title'],
                        "state": item['state'],
                        "created_at": item['created_at'],
                        "author": item['user']['login'],
                        "body": item['body']
                    }
                else:
                    issue = {
                        "title": item['title'],
                        "created_at": item['created_at'],
                        "author": item['user']['login']
                    }

                issues.append(issue)

                if limit and len(issues) >= limit:
                    return issues

            page += 1

        return issues

    def get_metadata(self):
        """
        Get the repository's description and tags (topics).
        :return: A dictionary containing the repository's description and tags.
        """
        # We need to explicitly request the topics using a custom media type
        headers = self.headers.copy()
        headers["Accept"] = "application/vnd.github.mercy-preview+json"

        repo_data = requests.get(f"{self.BASE_URL}/repos/{self.github_repo}", headers=headers).json()

        return {
            "description": repo_data.get("description"),
            "tags": repo_data.get("topics", [])
        }

    def get_pull_requests(
            self,
            start_date=None,
            end_date=None,
            username=None,
            limit=None,
            open_only=False,
            detailed=False
    ):
        """
        Process pull requests within a specified date range and for a specific user.
        :param start_date: Start date for PR range (inclusive), in 'YYYY-MM-DD' format
        :param end_date: End date for PR range (inclusive), in 'YYYY-MM-DD' format
        :param username: GitHub username to filter PRs (optional)
        :param limit: Maximum number of PRs to retrieve (default is None, which retrieves all in range)
        :param open_only: If True, return only open pull requests (default is False)
        :param detailed: If True, include PR body in the result (default is False)
        :return: Dictionary of pull requests
        """
        params = {
            "state": "open" if open_only else "all",
            "per_page": 100,  # GitHub API max per page
            "sort": "created",
            "direction": "desc"
        }
        if start_date:
            params["since"] = f"{start_date}T00:00:00Z"

        pull_requests = {}
        page = 1
        while True:
            params["page"] = page
            page_items = self._make_request("pulls", params=params)
            if not page_items:
                break

            for item in page_items:
                created_at = datetime.strptime(item['created_at'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

                if end_date and created_at > datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59,
                                                                                             second=59,
                                                                                             tzinfo=timezone.utc):
                    continue
                if start_date and created_at < datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc):
                    return pull_requests  # Stop if we've passed the start date

                # Apply username filter
                if username and item['user']['login'] != username:
                    continue

                pr_info = {
                    "number": item['number'],
                    "title": item['title'],
                    "state": item['state'],
                    "created_at": item['created_at'],
                    "author": item['user']['login'],
                }

                if detailed:
                    pr_info["body"] = item['body']

                pull_requests[item['number']] = pr_info

                if limit and len(pull_requests) >= limit:
                    return pull_requests

            page += 1

        return pull_requests

    def get_pull_request_commits(self, pr_number):
        """
        Get commits for a specific pull request.
        :param pr_number: The number of the pull request
        :return: List of commits in the pull request
        """
        return self._make_request(f"pulls/{pr_number}/commits")

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

    def get_releases(self, limit=100):
        """
        Get the releases of the repository.
        :return: The list of the releases
        """
        return [
            {
                "name": release["name"],
                "version": release["tag_name"],
                "body": release["body"],
                "draft": release["draft"],
                "prerelease": release["prerelease"],
                "created_at": datetime.strptime(release["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                "published_at": datetime.strptime(release["published_at"], "%Y-%m-%dT%H:%M:%SZ"),
            }
            for release in self._make_request("releases", params={"per_page": limit})
        ]

    def get_structure(self, path='', branch=None, include_invisible=False):
        """
        Scan and return the file structure and file names of the GitHub repository as a list of paths.
        :param path: The path to start scanning from (default is root)
        :param branch: The branch to scan (if None, the repository's default branch will be used)
        :param include_invisible: Whether to include invisible files/folders (starting with .) (default is False)
        :return: A list of file paths in the repository
        """

        def traverse_tree(tree_sha, current_path):
            tree = self._make_request(f'git/trees/{tree_sha}')
            paths = []
            for item in tree['tree']:
                item_path = os.path.join(current_path, item['path'])
                if not include_invisible and item['path'].startswith('.'):
                    continue
                if item['type'] == 'tree':
                    paths.extend(traverse_tree(item['sha'], item_path))
                else:
                    paths.append(item_path)
            return paths

        # Get the SHA of the latest commit on the specified branch
        if branch is None:
            branch = self._make_request().get("default_branch", "main")

        branch_data = self._make_request(f'branches/{branch}')
        root_tree_sha = branch_data['commit']['commit']['tree']['sha']

        # If a specific path is provided, navigate to that path
        if path:
            current_path = ''
            for part in path.split('/'):
                current_path += f'/{part}' if current_path else part
                tree = self._make_request(f'contents/{current_path}', params={'ref': branch})
                if isinstance(tree, list):
                    for item in tree:
                        if item['path'] == path:
                            if item['type'] == 'dir':
                                root_tree_sha = item['sha']
                            else:
                                return [item['path']]
                elif isinstance(tree, dict):
                    if tree['type'] == 'file':
                        return [tree['path']]
                    else:
                        root_tree_sha = tree['sha']

        # Traverse the tree starting from the root or specified path
        return traverse_tree(root_tree_sha, path)

    def get_user_activity(self, username, start_date=None, end_date=None, detailed=True):
        """
        Aggregate information about a user's activity within a specific time period.
        :param username: GitHub username to analyze
        :param start_date: Start date for the analysis period, in 'YYYY-MM-DD' format
        :param end_date: End date for the analysis period, in 'YYYY-MM-DD' format
        :param detailed: If True, include detailed information about commits, PRs, and issues
        :return: Dictionary containing aggregated user activity information, if the
        start and end dates are not provided, the default period is the last 7 days.
        """
        if end_date is None:
            end_datetime = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59, microsecond=0)
            end_date = end_datetime.strftime("%Y-%m-%d")
        else:
            end_datetime = (datetime.strptime(end_date, "%Y-%m-%d")
                            .replace(hour=23, minute=59, second=59, tzinfo=timezone.utc))

        if start_date is None:
            start_datetime = end_datetime - timedelta(days=6)
            start_date = start_datetime.strftime("%Y-%m-%d")

        # Fetch data
        commits = self.get_commit_history(start_date, end_date, username)
        pull_requests = self.get_pull_requests(
            start_date=start_date,
            end_date=end_date,
            username=username,
            detailed=True
        )
        issues = self.get_issues(start_date=start_date, end_date=end_date, username=username)

        # Aggregate commit information
        commit_count = len(commits)
        commit_messages = [commit['message'] for commit in commits.values()]

        # Aggregate pull request information
        pr_count = len(pull_requests)
        pr_details = []
        for pr in pull_requests.values():
            pr_commits = self.get_pull_request_commits(pr['number'])
            pr_detail = {
                'number': pr['number'],
                'title': pr['title'],
                'status': pr['state'],
                'commit_count': len(pr_commits),
            }

            if detailed:
                pr_detail.update({
                    'description': pr['body'],
                    'commit_messages': [commit['commit']['message'] for commit in pr_commits]
                })

            pr_details.append(pr_detail)

        # Aggregate issue information
        issue_details = []
        issue_count = len(issues)
        for issue in issues:
            issue_detail = {
                'number': issue['number'],
                'title': issue['title'],
            }

            if detailed:
                issue_detail.update({'description': issue['body']})
            issue_details.append(issue_detail)

        # Compile the report
        report = {
            'username': username,
            'period': {
                'start': start_date,
                'end': end_date
            },
            'summary': {
                'total_commits': commit_count,
                'total_pull_requests': pr_count,
                'total_issues': issue_count
            },
            'commits': {
                'count': commit_count,
                'messages': commit_messages
            },
            'pull_requests': {
                'count': pr_count,
                'details': pr_details
            },
            'issues': {
                'count': issue_count,
                'details': issue_details
            }
        }

        return report
