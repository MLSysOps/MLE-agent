import requests
from rich.console import Console

console = Console()


def kaggle_url_to_text(url: str):
    """
    Fetches content from the given URL using Jina Reader and returns it as a dictionary.
    """
    SECTIONS = ["overview", "data"]
    text_dict = {}
    for section in SECTIONS:
        for i in range(2):
            # Retry 3 times if the request fails
            # TODO (zhz): sometimes the first scrape fails, but the second one works
            console.log(f"[red]{i + 1}[/red]: Trying to fetch {section} from {url}")
            try:
                reader_url = f"https://r.jina.ai/{url}/{section}"
                response = requests.get(reader_url)
                response.raise_for_status()
                text_dict[section] = response.text
            except requests.exceptions.HTTPError:
                continue
    return text_dict['overview'], text_dict['data']
