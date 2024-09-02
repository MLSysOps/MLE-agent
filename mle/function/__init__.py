from .data import *
from .files import *
from .search import *
from .execution import *
from .interaction import *

# File system related functions schemas
schema_read_file = {
    'name': 'read_file',
    'description': 'Read the contents of a file and return it as a string. '
                   'Use this function when there is a need to check an existing file.',
    'parameters': {
        'type': 'object',
        'properties': {
            'file_path': {
                'type': 'string',
                'description': 'The path of the file to read'
            }
        }
    }
}

schema_create_file = {
    'name': 'create_file',
    'description': 'Create a file with the given path and content.'
                   'Use this function when there is a need to create a new file with initial content.',
    'parameters': {
        'type': 'object',
        'properties': {
            'path': {
                'type': 'string',
                'description': 'The path to the file to create'
            },
            'content': {
                'type': 'string',
                'description': 'The initial content to write to the file'
            }
        }
    }
}

schema_write_file = {
    'name': 'write_file',
    'description': 'Write content to a file. '
                   'Use this function when there is a need to write content to an existing file.',
    'parameters': {
        'type': 'object',
        'properties': {
            'path': {
                'type': 'string',
                'description': 'The path to the file to write to'
            },
            'content': {
                'type': 'string',
                'description': 'The content to write to the file'
            }
        }
    }
}

schema_list_files = {
    'name': 'list_files',
    'description': 'Lists all files and directories under the given path if it is a directory. '
                   'Use this function when there is a need to list the contents of a directory. ',
    'parameters': {
        'type': 'object',
        'properties': {
            'path': {
                'type': 'string',
                'description': 'The file system path to check and list contents from'
            }
        }
    }
}

schema_create_directory = {
    'name': 'create_directory',
    'description': 'Create a directory if it does not exist. '
                   'Use this function when there is a need to create a new directory.',
    'parameters': {
        'type': 'object',
        'properties': {
            'path': {
                'type': 'string',
                'description': 'The path of the directory to create'
            }
        }
    }
}

# Web search related function schema
schema_web_search = {
    'name': 'web_search',
    'description': 'Perform a web search and return a concise answer along with relevant sources. '
                   'Use this function when there is a need to search for information on the web.',
    'parameters': {
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': 'The search query to perform'
            }
        }
    }
}

schema_search_arxiv = {
    'name': 'search_arxiv',
    'description': 'Search for papers on arXiv and return the top results based on keywords'
                   ' (task, model, dataset, etc.) Use this function when there is a need to search'
                   ' for research papers.',
    'parameters': {
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': 'The search query to perform'
            },
            'max_results': {
                'type': 'integer',
                'description': 'The maximum number of results to return'
            }
        }
    }
}

schema_search_papers_with_code = {
    'name': 'search_papers_with_code',
    'description': 'Search for papers on Papers with Code and return the top results based on keywords'
                   ' (task, model, dataset, etc.) Use this function when there is a need to search'
                   ' for research papers and the source code.',
    'parameters': {
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': 'The search query to perform'
            },
            'k': {
                'type': 'integer',
                'description': 'The maximum number of results to return'
            }
        }
    }
}

schema_search_github_repos = {
    'name': 'search_github_repos',
    'description': 'Search for repositories on GitHub based on the given query. '
                   'Use this function when there is a need to search for repositories on GitHub.',
    'parameters': {
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': 'The string query to search for in repository names or descriptions'
            },
            'limit': {
                'type': 'integer',
                'description': 'The total number of repositories to return, default is 5'
            }
        }
    }
}

# Code execution related function schema
schema_execute_command = {
    'name': 'execute_command',
    'description': 'Execute a command in the system shell. '
                   'Use this function when there is a need to run a system command, and execute programs.',
    'parameters': {
        'type': 'object',
        'properties': {
            'command': {
                'type': 'string',
                'description': 'The command to execute in the system shell'
            }
        }
    }
}

# Interaction related function schema
schema_ask_question = {
    'name': 'ask_question',
    'description': 'Ask a question to the user and get a response. '
                   'Use this function when there is a need to interact with the user by asking questions.',
    'parameters': {
        'type': 'object',
        'properties': {
            'question': {
                'type': 'string',
                'description': 'The question to ask the user'
            }
        }
    }
}

schema_ask_yes_no = {
    'name': 'ask_yes_no',
    'description': 'Ask a yes/no question to the user and get a response. '
                   'Use this function when there is a need to ask the user a yes/no question.',
    'parameters': {
        'type': 'object',
        'properties': {
            'question': {
                'type': 'string',
                'description': 'The yes/no question to ask the user'
            }
        }
    }
}

schema_ask_choices = {
    'name': 'ask_choices',
    'description': 'Ask a multiple-choice question to the user and get a response. '
                   'Use this function when there is a need to ask the user to choose from multiple options.',
    'parameters': {
        'type': 'object',
        'properties': {
            'question': {
                'type': 'string',
                'description': 'The multiple-choice question to ask the user'
            },
            'choices': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'description': 'The list of choices for the user to select from'
            }
        }
    }
}

# Data preview related function schema
schema_preview_csv_data = {
    'name': 'preview_csv_data',
    'description': 'Preview the contents of a CSV file and return the first few rows. '
                   'Use this function when there is a need to preview the data in a CSV file.',
    'parameters': {
        'type': 'object',
        'properties': {
            'path': {
                'type': 'string',
                'description': 'The path of the CSV file to preview'
            },
            'limit_rows': {
                'type': 'integer',
                'description': 'The number of rows to preview, should not be a very large number. Default is 3.'
            }
        }
    }
}

# Mapping of function names to function schemas
FUNCTION_NAMES = [
    'read_file',
    'create_file',
    'write_file',
    'list_files',
    'create_directory',
    'web_search',
    'search_arxiv',
    'search_papers_with_code',
    'search_github_repos',
    'execute_command',
    'ask_question',
    'ask_yes_no',
    'ask_choices',
    'preview_csv_data'
]

FUNCTIONS = [
    read_file,
    create_file,
    write_file,
    list_files,
    create_directory,
    web_search,
    search_arxiv,
    search_papers_with_code,
    search_github_repos,
    execute_command,
    ask_question,
    ask_yes_no,
    ask_choices,
    preview_csv_data
]

SEARCH_FUNCTIONS = [
    "web_search",
    "search_arxiv",
    "search_papers_with_code",
    "search_github_repos"
]


# Function related utility functions
def get_function(function_name: str):
    """
    Get the function schema by the given function name.
    :param function_name: the function name.
    :return: the function schema.
    """
    for func in FUNCTIONS:
        if func.__name__ == function_name:
            return func

    raise ValueError(f"Function {function_name} is not supported.")


def process_function_name(function_name: str):
    """
    Process the function name to avoid the LLM handling errors.
    :param function_name: the generated function name.
    :return: the correct function name.
    """
    for func in FUNCTION_NAMES:
        if func in function_name:
            return func

    raise ValueError(f"Function {function_name} is not supported.")
