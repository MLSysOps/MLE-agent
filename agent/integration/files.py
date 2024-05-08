import os
from instructor import OpenAISchema
from pydantic import Field


class ReadPathFunc(OpenAISchema):
    """
    Given a path to a code file, the function will read the raw content of the code file and return it.
    If the user provides a directory path, the function will return the list of files in the directory.
    """

    file_path: str = Field(
        ...,
        example='/Users/home/desktop/project/read_s3_data.py',
        descriptions="read the content of read_s3_data.py",
    )

    class Config:
        title = "read_path_content"

    @classmethod
    def execute(cls, file_path):
        if os.path.isfile(file_path):
            with open(file_path, 'r') as file:
                return file.read()
        elif os.path.isdir(file_path):
            return os.listdir(file_path)
        else:
            return "Invalid path provided."
