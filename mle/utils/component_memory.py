"""
Component Memory System for MLE-Agent.

This module provides functionality for tracking, storing, and retrieving
execution traces of different components in the MLE-Agent system.
"""

import os
import json
import uuid
import time
import sqlite3
import traceback
import functools
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple


class ComponentMemory:
    """
    Tracks and stores execution traces for different components in MLE-Agent.
    
    Uses SQLite as the backend for efficient storage and querying of component traces.
    Each component type has its own table, and traces can be queried by component,
    timestamp, or content.
    """
    
    def __init__(self, project_dir: str):
        """
        Initialize the component memory system.
        
        Args:
            project_dir: The project directory path.
        """
        self.project_dir = project_dir
        
        # Ensure the .mle directory exists
        self.memory_dir = os.path.join(project_dir, '.mle')
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # Initialize SQLite database for storing traces
        self.db_path = os.path.join(self.memory_dir, 'component_traces.db')
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Access rows by name
        
        # Initialize tables
        self._initialize_tables()
    
    def _initialize_tables(self):
        """Initialize the database tables for storing component traces."""
        cursor = self.conn.cursor()
        
        # Create a table for each component type
        components = [
            'advisor', 'planner', 'coder', 'debugger', 'reporter', 'chat', 
            'github_summarizer', 'git_summarizer'
        ]
        
        for component in components:
            cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {component}_traces (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                project_name TEXT,
                input_data TEXT,
                output_data TEXT,
                execution_time REAL,
                context TEXT,
                status TEXT
            )
            ''')
        
        # Create a table for tracking relationships between traces
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trace_relationships (
            source_id TEXT,
            target_id TEXT,
            relationship_type TEXT,
            metadata TEXT,
            PRIMARY KEY (source_id, target_id, relationship_type)
        )
        ''')
        
        self.conn.commit()
    
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
        
        # Serialize complex data types
        input_json = self._serialize_data(input_data)
        output_json = self._serialize_data(output_data)
        context_json = self._serialize_data(context or {})
        
        # Store in the appropriate table
        cursor = self.conn.cursor()
        query = f'''
        INSERT INTO {component}_traces 
        (id, timestamp, project_name, input_data, output_data, execution_time, context, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        cursor.execute(query, (
            trace_id, 
            timestamp, 
            project_name, 
            input_json, 
            output_json, 
            execution_time,
            context_json,
            status
        ))
        
        self.conn.commit()
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
        cursor = self.conn.cursor()
        query = f"SELECT * FROM {component}_traces WHERE id = ?"
        cursor.execute(query, (trace_id,))
        
        row = cursor.fetchone()
        if row:
            return self._row_to_dict(row)
        return None
    
    def get_recent_traces(self, component: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent traces for a component.
        
        Args:
            component: The component type.
            limit: Maximum number of traces to return.
            
        Returns:
            List[Dict]: List of trace data dictionaries.
        """
        cursor = self.conn.cursor()
        query = f"SELECT * FROM {component}_traces ORDER BY timestamp DESC LIMIT ?"
        cursor.execute(query, (limit,))
        
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
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
        cursor = self.conn.cursor()
        query = f'''
        SELECT * FROM {component}_traces 
        WHERE input_data LIKE ? OR output_data LIKE ? 
        ORDER BY timestamp DESC LIMIT ?
        '''
        search_pattern = f"%{search_text}%"
        cursor.execute(query, (search_pattern, search_pattern, limit))
        
        return [self._row_to_dict(row) for row in cursor.fetchall()]
    
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
        cursor = self.conn.cursor()
        metadata_json = self._serialize_data(metadata or {})
        
        try:
            cursor.execute('''
            INSERT INTO trace_relationships
            (source_id, target_id, relationship_type, metadata)
            VALUES (?, ?, ?, ?)
            ''', (source_id, target_id, relationship_type, metadata_json))
            
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Relationship already exists
            return False
    
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
        cursor = self.conn.cursor()
        
        if relationship_type:
            query = '''
            SELECT * FROM trace_relationships 
            WHERE source_id = ? AND relationship_type = ?
            '''
            cursor.execute(query, (trace_id, relationship_type))
        else:
            query = '''
            SELECT * FROM trace_relationships 
            WHERE source_id = ?
            '''
            cursor.execute(query, (trace_id,))
        
        relationships = []
        for row in cursor.fetchall():
            rel = {
                'source_id': row['source_id'],
                'target_id': row['target_id'],
                'relationship_type': row['relationship_type'],
                'metadata': json.loads(row['metadata'])
            }
            relationships.append(rel)
            
        return relationships
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
    
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
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert an SQLite row to a dictionary with deserialized data."""
        trace = dict(row)
        
        # Deserialize JSON fields
        trace['input_data'] = self._deserialize_data(trace['input_data'])
        trace['output_data'] = self._deserialize_data(trace['output_data'])
        trace['context'] = self._deserialize_data(trace['context'])
        
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