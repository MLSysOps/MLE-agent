import requests
from fastapi import HTTPException
from rich.console import Console

from agent.types import SearchEngine
from agent.utils import Config

config = Config()


class SearchAgent:
    def __init__(self):
        self.console = Console()
        config_dict = config.read()
        self.engine_name = config_dict['general']['search_engine']

        if not self.engine_name:
            self.console.log("Search engine is not set.")
            raise NotImplementedError("Search engine is not set.")

        search_engine = config.read().get(self.engine_name)
        search_engine['name'] = self.engine_name

        self.search_engine = SearchEngine.validate(search_engine)
        print(self.search_engine)

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
        if self.engine_name == "google":
            return self.search_with_google(query)
        else:
            self.console.log(f"Search engine {self.engine_name} is not supported.")
            raise HTTPException(400, "Search engine not supported.")


if __name__ == "__main__":
    search_agent = SearchAgent()
    print(search_agent.invoke("mle-agent"))
