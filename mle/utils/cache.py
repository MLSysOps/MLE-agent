import pickle
from typing import Dict, Any, Optional
from datetime import datetime

from mle.utils.system import get_config, write_config


class WorkflowCacheOperator:
    """
    WorkflowCacheOperator handles the storing and resuming of cache content.
    """

    def __init__(self, cache: 'WorkflowCache', cache_content: Dict[str, Any]):
        """
        Args:
            cache: The cache instance to which this operator belongs.
            cache_content (Dict[str, object]): A dictionary holding the cached content.
        """
        self.cache = cache
        self.cache_content = cache_content

    def store(self, key: str, value: Any) -> None:
        """
        Store a value into the cache content.

        Args:
            key (str): The key under which the value is stored.
            value (object): The value to be stored.
        """
        self.cache_content[key] = pickle.dumps(value, fix_imports=False)

    def resume(self, key: str) -> Any:
        """
        Resume a value from the cache content.

        Args:
            key (str): The key of the value to be resumed.

        Returns:
            object: The resumed value, or None if the key does not exist.
        """
        if key in self.cache_content:
            return pickle.loads(self.cache_content[key])
        return None

    def __enter__(self):
        """
        Enter the runtime context related to this object.

        Returns:
            WorkflowCacheOperator: self
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the runtime context related to this object.

        Args:
            exc_type: The exception type.
            exc_val: The exception value.
            exc_tb: The traceback object.
        """
        if exc_type is None:
            self.cache._store_cache_buffer()


class WorkflowCache:
    """
    WorkflowCache manages the caching for workflows, providing
    methods to load, store, and remove cached steps.
    """

    def __init__(self, project_dir: str, workflow: str = 'baseline'):
        """
        Initialize WorkflowCache with a project directory.

        Args:
            project_dir (str): The directory of the project.
            workflow (str): The name of the cached workflow.
        """
        self.project_dir = project_dir
        self.workflow = workflow
        self.buffer = self._load_cache_buffer(workflow)
        self.cache: Dict[int, Dict[str, Any]] = self.buffer["cache"][workflow]

    def is_empty(self) -> bool:
        """
        Check if the cache is empty.

        Returns:
            bool: True if the cache is empty, False otherwise.
        """
        return len(self.cache) == 0

    def remove(self, step: int) -> None:
        """
        Remove a step from the cache.

        Args:
            step (int): The step index to be removed.
        """
        self.cache.pop(step, None)
        self._store_cache_buffer()

    def current_step(self) -> int:
        """
        Get the current step from the cache.

        Returns:
            int: The current step.
        """
        return max(self.cache.keys()) if self.cache else 0

    def resume_variable(self, key: str, step: Optional[int] = None):
        """
        Resume the cached variable.

        Args:
            key (str): The key of the value to be resumed.
            step (str): The step to be initialized.

        Returns:
            object: The resumed value, or None if the key does not exist.
        """
        if step is not None:
            return self.__call__(step).resume(key)
        else:
            for step in range(self.current_step() + 1):
                value = self.resume_variable(key, step)
                if value is not None:
                    return value
            return None

    def _load_cache_buffer(self, workflow: str) -> Dict[str, Any]:
        """
        Load the cache buffer from the configuration.

        Args:
            workflow (str): The name of the cached workflow.

        Returns:
            dict: The buffer loaded from the configuration.
        """
        buffer = get_config() or {}
        if "cache" not in buffer.keys():
            buffer["cache"] = {}
        if workflow not in buffer["cache"].keys():
            buffer["cache"][workflow] = {}
        return buffer

    def _store_cache_buffer(self) -> None:
        """
        Store the cache buffer to the configuration.
        """
        write_config(self.buffer)

    def __call__(self, step: int, name: Optional[str] = None) -> WorkflowCacheOperator:
        """
        Initialize the cache content for a given step and name.

        Args:
            step (str): The step to be initialized.
            name (str): The name associated with the step.

        Returns:
            WorkflowCacheOperator: An instance of WorkflowCacheOperator.
        """
        if step not in self.cache.keys():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cache[step] = {
                "step": step,
                "name": name,
                "time": timestamp,
                "content": {},
            }
        cache_content = self.cache[step]["content"]
        return WorkflowCacheOperator(self, cache_content)

    def __str__(self) -> str:
        """
        Return a string representation of the step cache list.

        Returns:
            str: The string representation of the cache.
        """
        return "\n".join(f"[{k}] {v['name']} ({v['time']})" for k, v in self.cache.items())