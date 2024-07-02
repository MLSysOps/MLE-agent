"""
Search API functions based on Tavily.
"""
from tavily import TavilyClient


def web_search(api_key, query):
    """
    Perform a web search based on the query.
    Args:
        api_key: The API key for the Tavily search engine.
        query: The search query.
    """
    try:
        client = TavilyClient(api_key=api_key)
        response = client.qna_search(query=query, search_depth="advanced")
        return response
    except Exception as e:
        return f"Error performing web search: {str(e)}"
