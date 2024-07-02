from .files import *

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
