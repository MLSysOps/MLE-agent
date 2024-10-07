from git import Repo, NULL_TREE
from datetime import datetime, timedelta


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

    def get_commit_history(self, date_range=None, limit=None):
        """
        Get commit history from a git repository
        :param date_range: Number of days to look back from today (default None)
        :param limit: Number of commits to retrieve (default None)
        :return: List of commit history
        """
        try:
            commit_history = []
            for commit in self.repo.iter_commits(max_count=limit):
                commit_date = datetime.fromtimestamp(commit.committed_date)
                if date_range is None or (datetime.now() - commit_date).days <= date_range:
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
