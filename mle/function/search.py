"""
Search API functions based on Tavily.
"""
import os
from tavily import TavilyClient


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
