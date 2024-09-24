import os
import re
import uuid
import yaml
import base64
import shutil
import requests
import platform
import subprocess
import importlib.util
from typing import Dict, Any, Optional, Callable
from rich.panel import Panel
from rich.prompt import Prompt
from rich.console import Console


def dict_to_markdown(data: Dict[str, Any], file_path: str) -> None:
    """
    Write a dictionary to a markdown file.
    :param data: the dictionary to write.
    :param file_path: the file path to write the dictionary to.
    :return:
    """

    def write_item(k, v, indent_level=0):
        if isinstance(v, dict):
            md_file.write(f"{'##' * (indent_level + 1)} {k}\n")
            for sub_key, sub_value in v.items():
                write_item(sub_key, sub_value, indent_level + 1)
        elif isinstance(v, list):
            md_file.write(f"{'##' * (indent_level + 1)} {k}\n")
            for item in v:
                md_file.write(f"{'  ' * indent_level}- {item}\n")
        else:
            md_file.write(f"{'##' * (indent_level + 1)} {k}\n")
            md_file.write(f"{'  ' * indent_level}{v}\n")

    with open(file_path, 'w') as md_file:
        for key, value in data.items():
            write_item(key, value)
            md_file.write("\n")


def print_in_box(text: str, console: Optional[Console] = None, title: str = "", color: str = "white") -> None:
    """
    Print the text in a box.
    :param text: the text to print.
    :param console: the console to print the text.
    :param title: the title of the box.
    :param color: the border color.
    :return:
    """
    console = console or Console()

    panel = Panel(text, title=title, border_style=color, expand=True)
    console.print(panel)


def ask_text(question: str, title: str = "User", console: Optional[Console] = None) -> str:
    """
    Display a question in a panel and prompt the user for an answer.
    :param question: the question to display.
    :param title: the title of the panel.
    :param console: the console to use.
    :return: the user's answer.
    """
    console = console or Console()

    console.print(Panel(question, title="MLE Agent", border_style="purple"))
    answer = Prompt.ask(f"Type your answer here")
    console.print(Panel(answer, title=title))
    return answer


def check_config(console: Optional[Console] = None):
    """
    check_config: check if the configuration file exists.
    :return: True if the configuration file exists, False otherwise.
    """""
    console = console or Console()
    current_work_dir = os.getcwd()

    config_dir = os.path.join(current_work_dir, '.mle')
    config_path = os.path.join(config_dir, 'project.yml')

    # move the old config file to the new path for compatibility (delete in future)
    old_config_path = os.path.join(current_work_dir, 'project.yml')
    if os.path.exists(old_config_path):
        os.makedirs(config_dir, exist_ok=True)
        shutil.move(old_config_path, config_path)

    try:
        with open(config_path, 'r') as file:
            data = yaml.safe_load(file)
            if data is None:
                raise yaml.YAMLError
    except FileNotFoundError:
        console.log("Configuration file not found. Please run 'mle new' first.")
        return False
    except yaml.YAMLError:
        console.log("Configuration file could not be loaded.")
        return False

    if data.get('search_key'):
        os.environ["SEARCH_API_KEY"] = data.get('search_key')
    return True


def get_config(workdir: str = None) -> Optional[Dict[str, Any]]:
    """
    Get the configuration file.
    :workdir: the project directory.
    :return: the configuration file.
    """
    config_dir = os.path.join(workdir or os.getcwd(), '.mle')
    config_path = os.path.join(config_dir, 'project.yml')
    if not os.path.exists(config_path):
        return None

    with open(config_path, 'r') as file:
        return yaml.safe_load(file)


def write_config(value: Dict[str, Any], workdir: str = None) -> None:
    """
    Write the configuration file.
    """
    config_dir = os.path.join(workdir or os.getcwd(), '.mle')
    config_path = os.path.join(config_dir, 'project.yml')
    os.makedirs(config_dir, exist_ok=True)
    with open(config_path, 'w') as file:
        yaml.dump(value, file, default_flow_style=False)


def delete_directory(path: str) -> bool:
    """
    delete_directory: delete a directory and all its contents.

    Args:
        path: The path to the directory to be deleted.
    """
    if os.path.exists(path):
        shutil.rmtree(path)
        return True
    else:
        return False


def get_directory_name(path: str) -> Optional[str]:
    """
    Get the directory name if the path is a directory.
    :param path: the path to check.
    :return: the directory name if it's a directory, otherwise None.
    """
    if os.path.isdir(path):
        return os.path.basename(path)
    else:
        return None


def extract_file_name(text: str) -> Optional[str]:
    """
    Extracts the file name from a given text string.

    Args:
    text (str): The text containing the file name.

    Returns:
    str: The extracted file name, or an empty string if no file name is found.
    """
    match = re.search(r'File Name: (\S+)', text)
    if match:
        return match.group(1)
    else:
        return None


def list_dir_structure(start_path: str) -> str:
    """
    List all files and directories under the given path.
    :param start_path: the path to start listing from.
    :return:
    """
    return_str = ""
    for root, dirs, files in os.walk(start_path):
        level = root.replace(start_path, '').count(os.sep)
        indent = ' ' * 4 * level
        subindent = ' ' * 4 * (level + 1)
        return_str += f'{indent}{os.path.basename(root)}/\n'
        for f in files:
            return_str += f'{subindent}{f}\n'

    return return_str


def load_file(filepath: str, base64_decode: bool = False) -> str:
    """
    Load content from a file or URL.
    :param filepath: The path to the file or a URL.
    :param base64_decode: Whether to decode the content from Base64 format.
    :return: The content of the file or URL as a decoded text string.
    """
    if filepath.startswith('http://') or filepath.startswith('https://'):
        response = requests.get(filepath)
        response.raise_for_status()
        text = response.text
    else:
        filepath = filepath.replace("file://", "")
        with open(filepath, 'r', encoding='utf-8') as file:
            text = file.read()

    if base64_decode:
        text = base64.b64decode(text).decode('utf-8')
    return text


def check_installed(name: str):
    """
    Check if a command-line tool is installed.
    """
    try:
        subprocess.run(['which', name], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False
    return True


def startup_web(host: str = "0.0.0.0", port: int = 3000):
    """
    Start up the web server.
    :param host: The host address for the web server. Default is "0.0.0.0".
    :param port: The port for the web server. Default is 3000.
    """
    webapp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '../web/')
    if not os.path.exists(webapp_dir):
        raise RuntimeError(f"Failed to find web application directory: {webapp_dir}")

    env = os.environ.copy()
    env['HOST'] = host
    env['PORT'] = str(port)

    run_kwargs = {
        "cwd": webapp_dir,
        "env": env,
        "check": True,
        # "stdout": subprocess.DEVNULL,
        # "stderr": subprocess.DEVNULL,
    }
    if check_installed("pnpm"):
        try:
            subprocess.run(['pnpm', 'install'], **run_kwargs)
            subprocess.run(['pnpm', 'dev'], **run_kwargs)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to start the web server: {e}")
    elif check_installed("npm"):
        try:
            subprocess.run(['npm', 'install'], **run_kwargs)
            subprocess.run(['npm', 'run', 'dev'], **run_kwargs)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to start the web server: {e}")
    else:
        raise RuntimeError(
            "Please install `npm` and `nodejs` before starting the web applications.\n"
            "Refer to: https://nodejs.org/en/download/package-manager"
        )


def get_user_id():
    """
    Get the unique user id of the current machine.
    """
    system = platform.system()
    username = None
    hostname = None

    if system == "Windows":
        username = os.getenv('USERNAME', 'root')
        hostname = os.getenv('COMPUTERNAME')
    else:
        username = os.getenv('USER', 'root')
        try:
            hostname = os.uname().nodename
        except AttributeError:
            import socket
            hostname = socket.gethostname()

    if username and hostname:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{hostname}-{username}"))
    else:
        return None


def get_session_id():
    """
    Get the session id of the current process.
    """
    pid = os.getpid()
    start = os.stat(__file__).st_ctime if os.path.exists(__file__) else 0
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{pid}-{start}"))


def get_langfuse_observer(
    secret_key: Optional[str] = None,
    public_key: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    host: Optional[str] = None,
):
    """
    Get the Langfuse observer.
    :param secret_key: Langfuse secret key.
    :param public_key: Langfuse public key.
    :param host: Optional host address, defaulting to 'https://us.cloud.langfuse.com'.
    """
    spec = importlib.util.find_spec("langfuse")
    if spec is None:
        raise ImportError(
            "It seems you didn't install langfuse. In order to enable the observer, "
            "please make sure `langfuse` Python package has been installed. "
            "More information, please refer to: https://python.reference.langfuse.com/langfuse"
        )

    if secret_key is None:
        secret_key = os.environ["LANGFUSE_SECRET_KEY"]
    if public_key is None:
        public_key = os.environ["LANGFUSE_PUBLIC_KEY"]
    if user_id is None:
        user_id = get_user_id()
    if session_id is None:
        session_id = get_session_id()
    if host is None:
        host = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")

    langfuse = importlib.import_module("langfuse.decorators")
    langfuse.langfuse_context.configure(
        secret_key=secret_key,
        public_key=public_key,
        host=host,
        enabled=True,
    )

    def _observe(fn: Callable):
        @langfuse.observe(as_type="generation")
        def _fn(cls, *args, **kwargs):
            model = getattr(cls.model, "model", None)
            messages = getattr(cls.model, "chat_history", (args, kwargs))
            response = fn(cls, *args, **kwargs)
            langfuse.langfuse_context.update_current_observation(
                model=model,
                input=messages,
                output=response,
                usage={
                    "input": len(str(messages)),
                    "output": len(str(response)),
                    "unit": "TOKENS",
                }
            )
            return response

        @langfuse.observe()
        def query(*args, **kwargs):
            langfuse.langfuse_context.update_current_trace(
                user_id=user_id,
                session_id=session_id,
            )
            return _fn(*args, **kwargs)
        return query

    return _observe
