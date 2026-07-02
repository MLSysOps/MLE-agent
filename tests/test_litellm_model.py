"""
Tests for the LiteLLM model provider.
"""
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

# Stub mle.function to avoid pulling pandas and other heavy deps
_fake_func = types.ModuleType("mle.function")
_fake_func.SEARCH_FUNCTIONS = []
_fake_func.get_function = lambda x: (lambda **kw: "mock_result")
_fake_func.process_function_name = lambda x: x
sys.modules["mle.function"] = _fake_func

from mle.model.litellm import LiteLLMModel


class TestLiteLLMModelInit(unittest.TestCase):

    @patch.dict(os.environ, {}, clear=True)
    @patch("importlib.util.find_spec", return_value=True)
    @patch("importlib.import_module")
    def test_init_with_explicit_params(self, mock_import, mock_spec):
        mock_openai_cls = MagicMock()
        mock_import.return_value = SimpleNamespace(OpenAI=mock_openai_cls)

        model = LiteLLMModel(
            api_key="sk-test-key",
            base_url="http://myproxy:4000/v1",
            model="claude-3-5-sonnet",
            temperature=0.3
        )

        mock_openai_cls.assert_called_once_with(
            api_key="sk-test-key",
            base_url="http://myproxy:4000/v1",
            timeout=60.0,
            max_retries=2,
        )
        self.assertEqual(model.model, "claude-3-5-sonnet")
        self.assertEqual(model.model_type, "LiteLLM")
        self.assertEqual(model.temperature, 0.3)

    @patch.dict(os.environ, {
        "LITELLM_API_KEY": "sk-from-env",
        "LITELLM_BASE_URL": "http://env-proxy:8000/v1"
    })
    @patch("importlib.util.find_spec", return_value=True)
    @patch("importlib.import_module")
    def test_init_from_env_vars(self, mock_import, mock_spec):
        mock_openai_cls = MagicMock()
        mock_import.return_value = SimpleNamespace(OpenAI=mock_openai_cls)

        model = LiteLLMModel()

        mock_openai_cls.assert_called_once_with(
            api_key="sk-from-env",
            base_url="http://env-proxy:8000/v1",
            timeout=60.0,
            max_retries=2,
        )
        self.assertEqual(model.model, "gpt-4o")

    @patch.dict(os.environ, {}, clear=True)
    @patch("importlib.util.find_spec", return_value=True)
    @patch("importlib.import_module")
    def test_init_defaults_when_no_config(self, mock_import, mock_spec):
        mock_openai_cls = MagicMock()
        mock_import.return_value = SimpleNamespace(OpenAI=mock_openai_cls)

        model = LiteLLMModel()

        mock_openai_cls.assert_called_once_with(
            api_key="",
            base_url="http://localhost:4000/v1",
            timeout=60.0,
            max_retries=2,
        )

    @patch("importlib.util.find_spec", return_value=None)
    def test_init_raises_when_openai_not_installed(self, mock_spec):
        with self.assertRaises(ImportError) as ctx:
            LiteLLMModel(api_key="key")
        self.assertIn("OpenAI package not found", str(ctx.exception))


def _make_model():
    with patch("importlib.util.find_spec", return_value=True), \
         patch("importlib.import_module") as mock_import:
        mock_openai_cls = MagicMock()
        mock_import.return_value = SimpleNamespace(OpenAI=mock_openai_cls)
        model = LiteLLMModel(api_key="test", base_url="http://proxy:4000/v1")
    return model


class TestLiteLLMModelQuery(unittest.TestCase):

    def test_simple_query_returns_content(self):
        model = _make_model()
        mock_resp = SimpleNamespace(
            content="Paris is the capital of France.",
            tool_calls=None
        )
        model.client.chat.completions.create = MagicMock(
            return_value=SimpleNamespace(choices=[SimpleNamespace(message=mock_resp)])
        )

        result = model.query([{"role": "user", "content": "What is the capital of France?"}])

        self.assertEqual(result, "Paris is the capital of France.")
        call_kwargs = model.client.chat.completions.create.call_args
        self.assertEqual(call_kwargs.kwargs["model"], "gpt-4o")
        self.assertFalse(call_kwargs.kwargs["stream"])

    def test_query_with_none_content(self):
        model = _make_model()
        mock_resp = SimpleNamespace(content=None, tool_calls=None)
        model.client.chat.completions.create = MagicMock(
            return_value=SimpleNamespace(choices=[SimpleNamespace(message=mock_resp)])
        )

        result = model.query([{"role": "user", "content": "test"}])
        self.assertIsNone(result)

    def test_query_auth_error_propagates(self):
        model = _make_model()
        from openai import AuthenticationError
        model.client.chat.completions.create = MagicMock(
            side_effect=AuthenticationError(
                message="Invalid API key",
                response=MagicMock(status_code=401),
                body=None
            )
        )

        with self.assertRaises(AuthenticationError):
            model.query([{"role": "user", "content": "test"}])

    def test_query_rate_limit_error_propagates(self):
        model = _make_model()
        from openai import RateLimitError
        model.client.chat.completions.create = MagicMock(
            side_effect=RateLimitError(
                message="Rate limit exceeded",
                response=MagicMock(status_code=429),
                body=None
            )
        )

        with self.assertRaises(RateLimitError):
            model.query([{"role": "user", "content": "test"}])

    def test_query_timeout_propagates(self):
        model = _make_model()
        from openai import APITimeoutError
        model.client.chat.completions.create = MagicMock(
            side_effect=APITimeoutError(request=MagicMock())
        )

        with self.assertRaises(APITimeoutError):
            model.query([{"role": "user", "content": "test"}])

    def test_query_empty_choices_raises(self):
        model = _make_model()
        model.client.chat.completions.create = MagicMock(
            return_value=SimpleNamespace(choices=[])
        )

        with self.assertRaises(IndexError):
            model.query([{"role": "user", "content": "test"}])


class TestLiteLLMModelStream(unittest.TestCase):

    def test_stream_yields_content_chunks(self):
        model = _make_model()
        chunks = [
            SimpleNamespace(choices=[SimpleNamespace(
                delta=SimpleNamespace(content="Hello", tool_calls=None)
            )]),
            SimpleNamespace(choices=[SimpleNamespace(
                delta=SimpleNamespace(content=" world", tool_calls=None)
            )]),
        ]
        model.client.chat.completions.create = MagicMock(return_value=iter(chunks))

        result = list(model.stream([{"role": "user", "content": "test"}]))
        self.assertEqual(result, ["Hello", " world"])

    def test_stream_handles_none_content_chunks(self):
        model = _make_model()
        chunks = [
            SimpleNamespace(choices=[SimpleNamespace(
                delta=SimpleNamespace(content=None, tool_calls=None)
            )]),
            SimpleNamespace(choices=[SimpleNamespace(
                delta=SimpleNamespace(content="data", tool_calls=None)
            )]),
        ]
        model.client.chat.completions.create = MagicMock(return_value=iter(chunks))

        result = list(model.stream([{"role": "user", "content": "test"}]))
        self.assertEqual(result, [None, "data"])


class TestLiteLLMModelToolConversion(unittest.TestCase):

    def test_convert_functions_to_tools(self):
        model = _make_model()
        functions = [{
            "name": "get_weather",
            "description": "Get current weather",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"]
            }
        }]
        tools = model._convert_functions_to_tools(functions)

        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["type"], "function")
        self.assertEqual(tools[0]["function"]["name"], "get_weather")

    def test_convert_empty_functions(self):
        model = _make_model()
        self.assertEqual(model._convert_functions_to_tools([]), [])

    def test_convert_function_without_description(self):
        model = _make_model()
        tools = model._convert_functions_to_tools([{"name": "test", "parameters": {"type": "object"}}])
        self.assertEqual(tools[0]["function"]["description"], "")


if __name__ == "__main__":
    unittest.main()
