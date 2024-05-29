import requests

from fastapi import HTTPException

from .base_agent import BaseAgent


class SearchAgent(BaseAgent):

    def search_with_google(self, query: str):
        """
        https://developers.google.com/custom-search/v1/using_rest
        """
        params = {
            "key": self.search_engine.search_key,
            "cx": self.search_engine.cx,
            "q": query,
            "num": self.search_engine.refer_count
        }
        response = requests.get(
            self.search_engine.endpoint, params=params, timeout=self.search_engine.timeout
        )
        if not response.ok:
            self.console.error(f"{response.status_code} {response.text}")
            raise HTTPException(response.status_code, "Search engine error.")
        json_content = response.json()
        try:
            contexts = json_content["items"][:self.search_engine.refer_count]
        except KeyError:
            self.console.error(f"Error encountered: {json_content}")
            return []
        return contexts

    def invoke(self, query: str):
        """
        Invoke the search agent.
        """
        if self.search_engine.name == "google":
            return self.search_with_google(query)
        else:
            self.console.error(f"Search engine {self.search_engine.name} is not supported.")
            raise HTTPException(400, "Search engine not supported.")


if __name__ == "__main__":
    search_agent = SearchAgent()
    search_agent.invoke("test")