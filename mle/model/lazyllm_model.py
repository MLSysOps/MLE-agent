"""
LazyLLM Model Integration for MLE-agent

This module provides a unified interface for multiple LLM providers through LazyLLM.
It supports both online (cloud) and local (self-hosted) models.

Supported Providers:
- Online: OpenAI, Anthropic, Gemini, DeepSeek, Qwen, GLM, Kimi, MiniMax, Doubao, etc.
- Local: vLLM, LMDeploy, Ollama, etc.

Usage:
    from mle.model import LazyLLMModel
    model = LazyLLMModel(model='gpt-4o', api_key='your-api-key')
    response = model.query(chat_history)
"""

import os
import importlib.util
from mle.model.common import Model


class LazyLLMModel(Model):
    """
    LazyLLM-backed model class for unified LLM provider support.
    
    LazyLLM automatically handles:
    - Provider selection and configuration
    - Online vs local model detection
    - API key management with MLE_ namespace prefix
    - Model-specific parameter formatting
    """
    
    def __init__(self, model=None, source=None, api_key=None, base_url=None, temperature=0.7):
        """
        Initialize the LazyLLM model.
        
        Args:
            model (str): Model name (e.g., 'gpt-4o', 'deepseek-chat', 'qwen-plus')
            source (str): Provider source (e.g., 'openai', 'deepseek', 'qwen'). 
                         If None, will be auto-detected from model name.
            api_key (str): API key. If None, will look for MLE_<SOURCE>_API_KEY env var.
            base_url (str): Custom base URL for the API endpoint.
            temperature (float): Sampling temperature (default: 0.7).
        """
        super().__init__()
        
        # Check LazyLLM dependency
        dependency = "lazyllm"
        spec = importlib.util.find_spec(dependency)
        if spec is not None:
            self.lazyllm = importlib.import_module(dependency)
        else:
            raise ImportError(
                "It seems you didn't install lazyllm. In order to enable LazyLLM integration, "
                "please install it via: pip install lazyllm"
            )
        
        self.model = model
        self.source = source
        self.temperature = temperature
        self.base_url = base_url
        self.model_type = 'LazyLLM'
        
        # Handle API key with MLE_ namespace prefix
        self.api_key = self._get_api_key(api_key, source)
        
        # Initialize LazyLLM AutoModel (automatically selects OnlineModule or TrainableModule)
        self._init_model()
        
        self.func_call_history = []
    
    def _get_api_key(self, api_key, source):
        """
        Get API key from parameter or environment variable with MLE_ namespace prefix.
        
        Priority:
        1. Explicit api_key parameter
        2. MLE_<SOURCE>_API_KEY environment variable
        3. <SOURCE>_API_KEY environment variable (fallback for compatibility)
        
        Args:
            api_key (str): API key from parameter
            source (str): Provider source name
            
        Returns:
            str: API key
        """
        if api_key:
            return api_key
        
        if source:
            # Try MLE_ namespace first
            env_key_name = f"MLE_{source.upper()}_API_KEY"
            api_key = os.getenv(env_key_name)
            
            if api_key:
                return api_key
            
            # Fallback to standard env var name
            standard_key_name = f"{source.upper()}_API_KEY"
            api_key = os.getenv(standard_key_name)
            
            if api_key:
                return api_key
        
        # Last resort: try common API key env vars
        common_keys = [
            "MLE_API_KEY",
            "LAZYLLM_API_KEY", 
            "OPENAI_API_KEY",  # Default fallback
        ]
        
        for key_name in common_keys:
            api_key = os.getenv(key_name)
            if api_key:
                return api_key
        
        return None
    
    def _init_model(self):
        """
        Initialize LazyLLM AutoModel with configuration.
        
        AutoModel automatically:
        1. Checks if model is available locally (TrainableModule)
        2. Falls back to online API (OnlineModule)
        3. Handles provider-specific configuration
        """
        try:
            # Use LazyLLM's AutoModel for automatic model selection
            kwargs = {
                'model': self.model,
                'temperature': self.temperature,
            }
            
            if self.source:
                kwargs['source'] = self.source
            
            if self.api_key:
                # Set API key in environment for LazyLLM to pick up
                if self.source:
                    env_key_name = f"MLE_{self.source.upper()}_API_KEY"
                    os.environ[env_key_name] = self.api_key
            
            if self.base_url:
                kwargs['base_url'] = self.base_url
            
            # Create AutoModel instance
            self._model = self.lazyllm.AutoModel(**kwargs)
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize LazyLLM model: {e}")
    
    def query(self, chat_history, **kwargs):
        """
        Query the LLM model.
        
        Args:
            chat_history (list): List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters (e.g., max_tokens, top_p)
            
        Returns:
            str: Model response content
        """
        try:
            # LazyLLM models accept messages in OpenAI format
            response = self._model.query(
                chat_history,
                temperature=self.temperature,
                **kwargs
            )
            return response
            
        except Exception as e:
            raise RuntimeError(f"LazyLLM query failed: {e}")
    
    def stream(self, chat_history, **kwargs):
        """
        Stream the output from the LLM model.
        
        Args:
            chat_history (list): List of message dictionaries
            **kwargs: Additional parameters
            
        Yields:
            str: Chunks of model response
        """
        try:
            for chunk in self._model.stream(
                chat_history,
                temperature=self.temperature,
                **kwargs
            ):
                yield chunk
                
        except Exception as e:
            raise RuntimeError(f"LazyLLM stream failed: {e}")
    
    def get_model_type(self):
        """
        Get the underlying model type (OnlineModule or TrainableModule).
        
        Returns:
            str: Model type description
        """
        if hasattr(self._model, 'model_type'):
            return self._model.model_type
        return 'LazyLLM'
