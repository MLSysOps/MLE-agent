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
        Initialize LazyLLM OnlineModule with configuration.
        
        OnlineModule is used for cloud API providers.
        For local models, TrainableModule would be used instead.
        """
        try:
            # Use LazyLLM's OnlineModule for cloud API providers
            # This avoids auto-downloading local models
            
            # Set API key in LazyLLM's expected environment variable format
            if self.api_key and self.source:
                # LazyLLM expects LAZYLLM_<SOURCE>_API_KEY or <SOURCE>_API_KEY
                lazyllm_key_name = f"LAZYLLM_{self.source.upper()}_API_KEY"
                os.environ[lazyllm_key_name] = self.api_key
                # Also set standard format as fallback
                standard_key_name = f"{self.source.upper()}_API_KEY"
                os.environ[standard_key_name] = self.api_key
            
            kwargs = {
                'model': self.model,
                'temperature': self.temperature,
            }
            
            if self.source:
                kwargs['source'] = self.source
            
            if self.base_url:
                kwargs['base_url'] = self.base_url
            
            # Create OnlineModule instance for cloud APIs
            # This is more reliable than AutoModel when no local models are configured
            self._model = self.lazyllm.OnlineModule(**kwargs)
            
        except Exception as e:
            # Fallback to AutoModel if OnlineModule fails
            try:
                self._model = self.lazyllm.AutoModel(**kwargs)
            except Exception as e2:
                raise RuntimeError(f"Failed to initialize LazyLLM model: {e2}")
    
    def query(self, chat_history, **kwargs):
        """
        Query the LLM model using LazyLLM's forward method.
        
        Args:
            chat_history (list): List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters (e.g., max_tokens, top_p)
            
        Returns:
            str: Model response content
        """
        try:
            # LazyLLM uses forward() with llm_chat_history parameter
            # First parameter (input) cannot be None, use empty string
            response = self._model.forward(
                '',  # Empty input, actual conversation is in llm_chat_history
                llm_chat_history=chat_history,
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
            # LazyLLM streaming is done via stream_output parameter
            for chunk in self._model.forward(
                '',  # Empty input
                llm_chat_history=chat_history,
                stream_output=True,
                **kwargs
            ):
                if chunk:  # Filter out empty chunks
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
