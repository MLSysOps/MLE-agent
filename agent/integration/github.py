import base64
import requests


def retrieve_repos(query, language, token):
    """
    Retrieve repositories from GitHub based on a query and language.

    Args:
        query (str): The search query string.
        language (str): The programming language to filter repositories.
        token (str): GitHub personal access token for authentication.

    Returns:
        list: A list of repository objects matching the query.
              Returns an empty list if no repositories found or if the request fails.
    """
    url = 'https://api.github.com/search/repositories'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    params = {'q': query} #{'q': f'language:{language} {query}'}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()['items']
    else:
        return None


def retrieve_repo_contents(owner, repo, path, token):
    """
    Retrieve the contents of a directory in a GitHub repository.

    Args:
        owner (str): The owner or organization of the repository.
        repo (str): The name of the GitHub repository.
        path (str): The path within the repository to fetch contents from.
        token (str): GitHub personal access token for authentication.

    Returns:
        list: A list of dictionaries representing the directory contents.
              Returns an empty list if the directory is empty or if the request fails.
    """
    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        contents = response.json()
        return contents
    else:
        return None


def retrieve_file_content(owner, repo, filepath, token):
    """
    Retrieve the content of a file in a GitHub repository.

    Args:
        owner (str): The owner or organization of the repository.
        repo (str): The name of the GitHub repository.
        filepath (str): The path to the file in the repository.
        token (str): GitHub personal access token for authentication.

    Returns:
        str: The decoded content of the file as a string.
             Returns None if the file is not found or if the request fails.
    """
    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{filepath}'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        file_info = response.json()
        if 'content' in file_info:
            # Decode base64 encoded content
            content_bytes = base64.b64decode(file_info['content'])
            content = content_bytes.decode('utf-8')
            return content
        else:
            return None
    else:
        return None
