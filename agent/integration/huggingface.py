import huggingface_hub as hf
from huggingface_hub import HfApi, ModelFilter


def download_readme(model_id):
    """
    Download the README of the specified model.

    Parameters:
    model_id (str): The model ID to download the README from.

    Returns:
    str: The README content of the specified model.
    """
    try:
        file_path = hf.hf_hub_download(model_id, 'README.md')
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except Exception as e:
        return f"An error occurred: {e}"


def get_top_downloaded_models(
        task_name: str,
        top_k=5,
        tags=None,
        language: str = None,
        library: str = None
):
    """
    Search for models based on the specified task and return the top-downloaded K model ids.

    Parameters:
    task_name (str): The task to search for (e.g., "text-classification", "translation").
    top_k (int): The number of top-downloaded model ids to return.
    tags (List, str): A string tag or a list of tags to filter models on the Hub by.
    language (str): A string or list of strings of languages, both by name and country code.
    library (str): A string or list of strings of foundational libraries models were originally trained from.

    Returns:
    list: A list of the top-downloaded model ids.
    """
    api = HfApi()

    try:
        models = list(
            api.list_models(
                filter=ModelFilter(
                    task=task_name,
                    tags=tags,
                    language=language,
                    library=library
                )
            )
        )

        if not models:
            return "No models found for the specified task."

        models_sorted = sorted(models, key=lambda x: x.downloads, reverse=True)
        return [model.id for model in models_sorted[:top_k]]
    except Exception as e:
        return f"An error occurred: {e}"
