"""
Search API functions based on Tavily.
"""
import os
import requests
from tavily import TavilyClient
from xml.etree import ElementTree


def web_search(query: str):
    """
    Perform a web search based on the query.
    Args:
        query: The search query.
    """
    print(f"[FUNC CALL] web_search({query})")
    try:
        client = TavilyClient(api_key=os.environ['SEARCH_API_KEY'])
        response = client.qna_search(query=query, search_depth="advanced")
        return response
    except Exception as e:
        return f"Error performing web search: {str(e)}"


def search_arxiv(query, max_results=5):
    print(f"[FUNC CALL] search_arxiv({query}, {max_results})")
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
