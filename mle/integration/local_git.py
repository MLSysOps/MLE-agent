from git import Repo, NULL_TREE
from datetime import datetime, timezone, timedelta

import os
import fnmatch
import subprocess

class GitIntegration:
    def __init__(self, path):
        self.repo_path = path
        self.repo = Repo(self.repo_path)
        if self.repo.bare:
            raise Exception("Repository is not valid or is bare.")

    def get_repo_status(self):
        """
        Get the status of a git repository
        :return: List of changed files
        """
        try:
            changed_files = []
            for diff in self.repo.index.diff(None):
                changed_files.append({
                    'file_path': diff.a_path,
                    'change_type': diff.change_type,
                    'author': self.repo.head.commit.author.name,
                    'date': datetime.fromtimestamp(self.repo.head.commit.committed_date).strftime("%Y-%m-%d %H:%M:%S")
                })

            return changed_files

        except Exception as e:
            return f"An error occurred: {str(e)}"

    def get_commit_history(self, start_date=None, end_date=None, email=None, limit=None):
        """
        Process commit history within a specified date range and for a specific user (email).
        :param start_date: Start date for commit range (inclusive), in 'YYYY-MM-DD' format
        :param end_date: End date for commit range (inclusive), in 'YYYY-MM-DD' format
        :param username: GitHub username to filter commits (optional)
        :param limit: Maximum number of commits to retrieve (default is None, which retrieves all commits in range)
        :return: Dictionary of commits
        """
        end_time = None
        if end_date is not None:
            end_time = f"{end_date}T23:59:59Z"

        start_time = None
        if start_date is not None:
            start_time = f"{start_date}T00:00:00Z"

        try:
            commit_history = []
            for commit in self.repo.iter_commits(max_count=limit):
                commit_date = datetime.fromtimestamp(commit.committed_date)
                commit_date = commit_date.replace(tzinfo=timezone.utc)
                if start_time is not None and commit_date < datetime.fromisoformat(start_time):
                    continue

                if end_time is not None and commit_date > datetime.fromisoformat(end_time):
                    continue
                
                if email is not None and commit.author.email != email:
                    continue

                commit_history.append({
                    'commit_hash': commit.hexsha,
                    'author': commit.author.name,
                    'email': commit.author.email,
                    'message': commit.message.strip(),
                    'date': commit_date.strftime("%Y-%m-%d %H:%M:%S")
                })

            return commit_history

        except Exception as e:
            return f"An error occurred: {str(e)}"

    def get_commit_diff(self, commit_hash, show_content=False):
        """
        Get the code changes for a specific commit
        :param commit_hash: The hash of the commit to get the changes for
        :param show_content: Boolean to determine if file content should be included (default False)
        :return: A dictionary containing the commit info and the code changes
        """
        try:
            commit = self.repo.commit(commit_hash)
            parent = commit.parents[0] if commit.parents else NULL_TREE

            diffs = parent.diff(commit)

            changes = {}
            for diff in diffs:
                if show_content:
                    if diff.a_blob and diff.b_blob:
                        a_content = diff.a_blob.data_stream.read().decode('utf-8', errors='ignore')
                        b_content = diff.b_blob.data_stream.read().decode('utf-8', errors='ignore')
                        changes[diff.a_path] = {
                            'change_type': 'modified',
                            'old_content': a_content,
                            'new_content': b_content
                        }
                    elif diff.a_blob:
                        changes[diff.a_path] = {
                            'change_type': 'deleted',
                            'old_content': diff.a_blob.data_stream.read().decode('utf-8', errors='ignore'),
                            'new_content': None
                        }
                    elif diff.b_blob:
                        changes[diff.b_path] = {
                            'change_type': 'added',
                            'old_content': None,
                            'new_content': diff.b_blob.data_stream.read().decode('utf-8', errors='ignore')
                        }
                else:
                    if diff.a_blob and diff.b_blob:
                        changes[diff.a_path] = {'change_type': 'modified'}
                    elif diff.a_blob:
                        changes[diff.a_path] = {'change_type': 'deleted'}
                    elif diff.b_blob:
                        changes[diff.b_path] = {'change_type': 'added'}

            commit_info = {
                'commit_hash': commit.hexsha,
                'author': commit.author.name,
                'email': commit.author.email,
                'message': commit.message.strip(),
                'date': datetime.fromtimestamp(commit.committed_date).strftime("%Y-%m-%d %H:%M:%S"),
                'changes': changes
            }

            return commit_info

        except Exception as e:
            return f"An error occurred: {str(e)}"

    def get_source_code(self, file_pattern="*"):
        """
        Process source code files in the repository.
        :param file_pattern: Wildcard pattern to filter files (e.g., "*.py" for Python files)
        :return: Dictionary with file paths as keys and file contents as values
        """

        def get_contents(path="", file_pattern=file_pattern):
            for root, _, files in os.walk(os.path.join(self.repo_path, path)):
                for filename in fnmatch.filter(files, file_pattern):
                    file_path = os.path.join(root, filename)
                    with open(file_path, 'r') as f:
                        yield {
                            'path': os.path.relpath(file_path, self.repo_path),
                            'name': filename,
                            'content': f.read()
                        }
        
        return {file['path']: file['content'] for file in get_contents()}

    def get_readme(self):
        """
        Get readme content of the repository.
        :return: The readme content
        """
        content = self.get_source_code("README.md")
        if len(content):
            return list(content.values())[0]
        return None

    def get_structure(self, path=''):
        """
        Scan and return the file structure and file names of the Git repository as a list of paths.
        :param path: The path to start scanning from (default is root)
        :param branch: The branch to scan (if None, the repository's default branch will be used)
        :param include_invisible: Whether to include invisible files/folders (starting with .) (default is False)
        :return: A list of file paths in the repository
        """
        result = subprocess.run(
            ["git", "-C", path, "ls-files"],
            stdout=subprocess.PIPE,
            text=True,
            check=True
        )
        
        return result.stdout.splitlines()

    def get_user_activity(self, email, start_date=None, end_date=None):
        """
        Aggregate information about a user's activity within a specific time period.
        :param email: User email to analyze
        :param start_date: Start date for the analysis period, in 'YYYY-MM-DD' format
        :param end_date: End date for the analysis period, in 'YYYY-MM-DD' format
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
        commits = self.get_commit_history(start_date, end_date, email)

        # Aggregate commit information
        commit_count = len(commits)
        commit_messages = [commit['message'] for commit in commits]

        # Compile the report
        report = {
            'username': email,
            'period': {
                'start': start_date,
                'end': end_date
            },
            'summary': {
                'total_commits': commit_count,
                'total_pull_requests': 0,
                'total_issues': 0
            },
            'commits': {
                'count': commit_count,
                'messages': commit_messages
            },
            'pull_requests': {
                'count': 0,
                'details': []
            },
            'issues': {
                'count': 0,
                'details': []
            }
        }

        return report
