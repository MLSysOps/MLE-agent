from .files import *
from .search import *
from .execution import *


def get_function(function_name: str):
    """
    Get the function schema by the given function name.
    :param function_name: the function name.
    :return: the function schema.
    """
    if function_name == 'read_file':
        return read_file
    elif function_name == 'create_file':
        return create_file
    elif function_name == 'write_file':
        return write_file
    elif function_name == 'list_files':
        return list_files
    elif function_name == 'create_directory':
        return create_directory
    elif function_name == 'web_search':
        return web_search
    elif function_name == 'execute_command':
        return execute_command
    else:
        raise ValueError(f"Function {function_name} is not supported.")


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
    'description': 'Create a file with the given path and content. '
                   'Use this function when there is a need to create a new file.',
    'parameters': {
        'type': 'object',
        'properties': {
            'path': {
                'type': 'string',
                'description': 'The path to the file to create'
            },
            'content': {
                'type': 'string',
                'description': 'The initial content to write to the file, default can be an empty string'
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
