import requests
from fastapi import HTTPException
from rich.console import Console

from agent.types import SearchEngine
from agent.utils import Config

config = Config()


class SearchAgent:
    def __init__(self, enable_web_search: bool = False):
        self.enable_web_search = enable_web_search
        self.console = Console()

        if not self.enable_web_search:
            self.console.log("Web search is disabled.")
            return

        else:
            config_dict = config.read()
            self.engine_name = config_dict['general'].get('search_engine')
            if not self.engine_name:
                self.console.log("No search engine is set.")
                return
            search_engine = config.read().get(self.engine_name)
            search_engine['name'] = self.engine_name

            self.search_engine = SearchEngine.validate(search_engine)

    def search_with_google(self, query: str):
        """
        https://developers.google.com/custom-search/v1/using_rest
        """
        params = {
            "key": self.search_engine.key,
            "cx": self.search_engine.cx,
            "q": query,
            "num": self.search_engine.refer_count
        }
        self.console.log(f"Searching with Google")
        response = requests.get(
            self.search_engine.endpoint, params=params, timeout=self.search_engine.timeout
        )
        if not response.ok:
            self.console.log(f"{response.status_code} {response.text}")
            raise HTTPException(response.status_code, "Search engine error.")
        json_content = response.json()
        try:
            contexts = json_content["items"][:self.search_engine.refer_count]
        except KeyError:
            self.console.log(f"Error encountered: {json_content}")
            return []
        return contexts

    def invoke(self, query: str):
        """
        Invoke the search agent.
        """
        if not self.enable_web_search:
            return ["no web search results for this query."]

        if self.engine_name == "google":
            return self.search_with_google(query)
        else:
            self.console.log(f"Search engine {self.engine_name} is not supported.")
            raise HTTPException(400, "Search engine not supported.")
