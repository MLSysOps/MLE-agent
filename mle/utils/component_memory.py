"""
Component Memory System for MLE-Agent.

This module provides functionality for tracking, storing, and retrieving
execution traces of different components in the MLE-Agent system.
"""

import os
import json
import uuid
import time
import traceback
import functools
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

from .memory import LanceDBMemory


class ComponentMemory:
    """
    Tracks and stores execution traces for different components in MLE-Agent.

    Uses LanceDB as the backend for efficient storage and querying of component traces.
    Component traces are organized by component type and can be queried by various attributes.
    """

    def __init__(self, project_dir: str):
        """
        Initialize the component memory system.

        Args:
            project_dir: The project directory path.
        """
        self.project_dir = project_dir
        
        # Initialize LanceDB memory as the backend storage
        self.memory = LanceDBMemory(project_dir)
        
        # Track components for easier access
        self.components = [
            'advisor', 'planner', 'coder', 'debugger', 'reporter', 'chat',
            'github_summarizer', 'git_summarizer'
        ]

    def store_trace(self,
                   component: str,
                   input_data: Any,
                   output_data: Any,
                   execution_time: float = None,
                   context: Dict[str, Any] = None,
                   status: str = 'success') -> str:
        """
        Store a component execution trace.

        Args:
            component: The component type (advisor, planner, coder, etc.).
            input_data: The input data to the component.
            output_data: The output data from the component.
            execution_time: The execution time in seconds.
            context: Additional context about the execution.
            status: The execution status (success, failure).

        Returns:
            str: The unique ID of the stored trace.
        """
        trace_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        project_name = os.path.basename(self.project_dir)
        
        # Prepare text representation for vector embedding
        # This combines the most important fields for semantic search
        if isinstance(input_data, str):
            input_text = input_data[:1000]  # Limit length for embedding
        else:
            input_text = str(input_data)[:1000]
            
        text_for_embedding = f"Component: {component}\nStatus: {status}\nInput: {input_text}"
        
        # Prepare metadata containing all trace details
        metadata = {
            "trace_id": trace_id,
            "component": component,
            "timestamp": timestamp,
            "project_name": project_name,
            "execution_time": execution_time,
            "status": status,
            "input_data": self._serialize_data(input_data),
            "output_data": self._serialize_data(output_data),
            "context": self._serialize_data(context or {})
        }
        
        # Store in the component-specific table
        table_name = f"component_{component}_traces"
        self.memory.add(
            texts=[text_for_embedding],
            metadata=[metadata],
            table_name=table_name,
            ids=[trace_id]
        )
        
        return trace_id

    def get_trace(self, component: str, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific trace by its ID.

        Args:
            component: The component type.
            trace_id: The trace ID.

        Returns:
            Dict or None: The trace data if found, None otherwise.
        """
        table_name = f"component_{component}_traces"
        results = self.memory.get(trace_id, table_name=table_name)
        
        if not results:
            return None
            
        return self._process_trace_result(results[0])

    def get_recent_traces(self, component: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent traces for a component.

        Args:
            component: The component type.
            limit: Maximum number of traces to return.

        Returns:
            List[Dict]: List of trace data dictionaries.
        """
        table_name = f"component_{component}_traces"
        
        # 1. Get all IDs
        # 2. Get metadata for each ID
        # 3. Sort by timestamp
        # 4. Take the most recent ones
        
        all_keys = self.memory.list_all_keys(table_name=table_name)
        if not all_keys:
            return []
            
        # Get all traces for this component
        traces = []
        for key in all_keys:
            result = self.memory.get(key, table_name=table_name)
            if result:
                traces.append(self._process_trace_result(result[0]))
        
        # Sort by timestamp (newest first)
        traces.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Return only the requested number
        return traces[:limit]

    def search_traces(self,
                     component: str,
                     search_text: str,
                     limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for traces containing specific text.

        Args:
            component: The component type.
            search_text: Text to search for in input or output.
            limit: Maximum number of traces to return.

        Returns:
            List[Dict]: List of matching trace dictionaries.
        """
        table_name = f"component_{component}_traces"
        
        # Use LanceDB's vector search capability
        results = self.memory.query(
            query_texts=[search_text],
            table_name=table_name,
            n_results=limit
        )
        
        if not results or not results[0]:
            return []
            
        return [self._process_trace_result(item) for item in results[0]]

    def add_relationship(self,
                        source_id: str,
                        target_id: str,
                        relationship_type: str,
                        metadata: Dict[str, Any] = None) -> bool:
        """
        Add a relationship between two traces.

        Args:
            source_id: The ID of the source trace.
            target_id: The ID of the target trace.
            relationship_type: The type of relationship.
            metadata: Additional metadata about the relationship.

        Returns:
            bool: True if relationship was added successfully.
        """
        relationship_id = f"{source_id}_{target_id}_{relationship_type}"
        
        relationship_text = f"Relationship: {relationship_type} from {source_id} to {target_id}"
        
        relationship_metadata = {
            "source_id": source_id,
            "target_id": target_id,
            "relationship_type": relationship_type,
            "metadata": self._serialize_data(metadata or {})
        }
        
        # Store in the relationships table
        table_name = "component_trace_relationships"
        self.memory.add(
            texts=[relationship_text],
            metadata=[relationship_metadata],
            table_name=table_name,
            ids=[relationship_id]
        )
        
        return True

    def get_related_traces(self,
                          trace_id: str,
                          relationship_type: str = None) -> List[Dict[str, Any]]:
        """
        Get traces related to a specific trace.

        Args:
            trace_id: The ID of the trace.
            relationship_type: Optional filter for relationship type.

        Returns:
            List[Dict]: List of related trace data.
        """
        table_name = "component_trace_relationships"
        
        # Get all relationships where this trace is the source
        if relationship_type:
            # Get relationships with specific type
            results = self.memory.query(
                query_texts=[f"Relationship: {relationship_type} from {trace_id}"],
                table_name=table_name,
                n_results=100  # Get many potential matches
            )
        else:
            # Get all relationships for this trace
            all_keys = self.memory.list_all_keys(table_name=table_name)
            results = []
            
            for key in all_keys:
                if key.startswith(f"{trace_id}_"):
                    rel = self.memory.get(key, table_name=table_name)
                    if rel:
                        results.append(rel[0])
        
        if not results or (isinstance(results, list) and not results[0]):
            return []
            
        # Process and return relationship data
        relationships = []
        for item in results if not isinstance(results[0], list) else results[0]:
            if 'metadata' in item and isinstance(item['metadata'], dict):
                rel_data = {
                    'source_id': item['metadata'].get('source_id'),
                    'target_id': item['metadata'].get('target_id'),
                    'relationship_type': item['metadata'].get('relationship_type'),
                    'metadata': json.loads(item['metadata'].get('metadata', '{}'))
                }
                relationships.append(rel_data)
        
        return relationships

    def close(self):
        """Close the memory connections."""
        pass

    def _serialize_data(self, data: Any) -> str:
        """Serialize data to JSON string."""
        try:
            return json.dumps(data)
        except TypeError:
            # Handle non-serializable objects
            return json.dumps(str(data))

    def _deserialize_data(self, json_str: str) -> Any:
        """Deserialize JSON string back to data."""
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return json_str
    
    def _process_trace_result(self, result: Dict) -> Dict[str, Any]:
        """Process a raw trace result from LanceDB into a standardized format."""
        if not result or 'metadata' not in result:
            return {}
            
        metadata = result['metadata']
        
        # Extract and deserialize the trace data
        trace = {
            'id': metadata.get('trace_id'),
            'component': metadata.get('component'),
            'timestamp': metadata.get('timestamp'),
            'project_name': metadata.get('project_name'),
            'execution_time': metadata.get('execution_time'),
            'status': metadata.get('status'),
            'input_data': self._deserialize_data(metadata.get('input_data', '{}')),
            'output_data': self._deserialize_data(metadata.get('output_data', '{}')),
            'context': self._deserialize_data(metadata.get('context', '{}'))
        }
        
        return trace


# Component tracing decorator
def trace_component(component_name: str):
    """
    Decorator for tracking component execution.

    Args:
        component_name: The name of the component (advisor, planner, etc.).

    Returns:
        The decorated function.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Determine project directory
            project_dir = getattr(self, "working_dir", None) or getattr(self, "project_path", None)
            if project_dir is None:
                project_dir = os.getcwd()

            # Initialize component memory
            memory = ComponentMemory(project_dir)

            # Capture input data
            input_data = args[0] if args else kwargs.get("requirement", None)
            if input_data is None and args:
                input_data = {"args": str(args)}

            # Capture context
            context = {
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys()) if kwargs else None,
                "project_dir": project_dir
            }

            # Record start time
            start_time = time.time()

            try:
                # Execute the function
                result = func(self, *args, **kwargs)

                # Calculate execution time
                execution_time = time.time() - start_time

                # Store successful trace
                trace_id = memory.store_trace(
                    component=component_name,
                    input_data=input_data,
                    output_data=result,
                    execution_time=execution_time,
                    context=context,
                    status='success'
                )

                # Close memory connection
                memory.close()

                return result

            except Exception as e:
                # Calculate execution time
                execution_time = time.time() - start_time

                # Store error trace
                error_data = {
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }

                trace_id = memory.store_trace(
                    component=component_name,
                    input_data=input_data,
                    output_data=error_data,
                    execution_time=execution_time,
                    context=context,
                    status='error'
                )

                # Close memory connection
                memory.close()

                # Re-raise the exception
                raise

        return wrapper
    return decorator