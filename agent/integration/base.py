from .files import ReadPathFunc


def get_function(name: str):
    """
    Get the function by name.
    :param name: the function name.
    :return: the function.
    """
    if name == "read_path_content":
        return ReadPathFunc
    return None


def get_all_func_schema():
    """
    Get all function schema.
    :return: a list of function schema.
    """
    return [ReadPathFunc.openai_schema]
