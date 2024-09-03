"""
Search API functions based on Tavily.
"""
import os
import requests
from tavily import TavilyClient
from xml.etree import ElementTree


def search_github_repos(query, limit=5):
    """
    Search GitHub public repositories based on a keyword.

    :param query: The query to search for in repository names or descriptions.
    :param limit: The total number of repositories to return.
    :return: A list of dictionaries containing repository details, limited to the specified number.
    """
    repos = []
    per_page = 10
    page = 1
    while len(repos) < limit:
        url = f'https://api.github.com/search/repositories?q={query}&per_page={per_page}&page={page}'

        response = requests.get(url)

        if response.status_code == 200:
            items = response.json().get('items', [])
            for item in items:
                formatted_repo = {
                    "name": f"{item['owner']['login']}/{item['name']}",
                    "author": item['owner']['login'],
                    "description": item['description'],
                    "link": item['html_url']
                }
                repos.append(formatted_repo)
                if len(repos) >= limit:
                    break

            if len(items) < per_page:  # Stop if there are no more repos to fetch
                break
            page += 1
        else:
            raise Exception(f"GitHub API request failed with status code {response.status_code}: {response.text}")

    return_str = """
    Here are some of the repositories I found on GitHub:
    """

    for repo in repos:
        return_str += f"""
        Name: {repo['name']}
        Description: {repo['description']}
        Link: {repo['link']}
        """

    return return_str


def web_search(query: str):
    """
    Perform a web search based on the query.
    Args:
        query: The search query.
    """
    try:
        client = TavilyClient(api_key=os.environ['SEARCH_API_KEY'])
        response = client.qna_search(query=query, search_depth="advanced")
        return response
    except Exception as e:
        return f"Error performing web search: {str(e)}"


def search_arxiv(query, max_results=8):
    url = 'https://export.arxiv.org/api/query'
    params = {
        'search_query': query,
        'start': 0,
        'max_results': max_results
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return f"Error: Unable to fetch data from arXiv (Status code: {response.status_code})"

    root = ElementTree.fromstring(response.content)
    output = ""
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        title = entry.find('{http://www.w3.org/2005/Atom}title').text
        summary = entry.find('{http://www.w3.org/2005/Atom}summary').text
        link = entry.find('{http://www.w3.org/2005/Atom}id').text
        published = entry.find('{http://www.w3.org/2005/Atom}published').text
        authors = [author.find('{http://www.w3.org/2005/Atom}name').text for author in
                   entry.findall('{http://www.w3.org/2005/Atom}author')]

        output += f"""
        Title: {title.strip()}
        Summary: {summary.strip()}
        Link: {link.strip()}
        Published: {published.strip()}
        Authors: {authors}
        """

    return output


def search_papers_with_code(query: str, k: int = 8) -> str:
    url = f"https://paperswithcode.com/api/v1/search/"
    response = requests.get(url, params={'page': 1, 'q': query})
    if response.status_code != 200:
        return "Failed to retrieve data from Papers With Code."

    data = response.json()
    if 'results' not in data:
        return "No results found for the given query."

    results = data['results'][:k]  # Get top-k results
    result_strings = []

    for result in results:
        paper = result['paper']
        paper_title = paper.get('title', 'No title available')
        abstract = paper.get('abstract', 'No abstract available')
        paper_pdf_url = paper.get('url_pdf', 'No PDF available')
        repository = result.get('repository', [])
        if repository:
            code_url = repository.get('url', 'No official code link available')
        else:
            code_url = 'No official code link available'

        result_string = f"Title: {paper_title}\nAbstract:{abstract}\nPaper URL: {paper_pdf_url}\nCode URL: {code_url}\n"
        result_strings.append(result_string)

    return "\n".join(result_strings)
