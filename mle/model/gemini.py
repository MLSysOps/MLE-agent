import os
import importlib.util
import json

from mle.function import SEARCH_FUNCTIONS, get_function, process_function_name
from mle.model.common import Model


class GeminiModel(Model):

    def __init__(self, api_key, model, temperature=0.7):
        """
        Initialize the Gemini model.
        Args:
            api_key (str): The Gemini API key.
            model (str): The model with version.
            temperature (float): The temperature value.
        """
        super().__init__()

        dependency = "google.generativeai"
        spec = importlib.util.find_spec(dependency)
        if spec is not None:
            self.gemini = importlib.import_module(dependency)
            self.gemini.configure(api_key=api_key)
        else:
            raise ImportError(
                "It seems you didn't install `google-generativeai`. "
                "In order to enable the Gemini client related features, "
                "please make sure gemini Python package has been installed. "
                "More information, please refer to: https://ai.google.dev/gemini-api/docs/quickstart?lang=python"
            )

        self.model = model if model else 'gemini-1.5-flash'
        self.model_type = 'Gemini'
        self.temperature = temperature
        self.func_call_history = []

    def _map_chat_history_from_openai(self, chat_history):
        _key_map_dict = {
            "role": "role",
            "content": "parts",
        }
        _value_map_dict = {
            "system": "model",
            "user": "user",
            "assistant": "model",
            "content": "parts",
        }
        return [
            {
                _key_map_dict.get(k, k): _value_map_dict.get(v, v)
                for k, v in dict(chat).items()
            } for chat in chat_history
        ]

    def _map_functions_from_openai(self, functions):
        def _mapping_type(_type: str):
            if _type == "string":
                return self.gemini.protos.Type.STRING
            if _type == "object":
                return self.gemini.protos.Type.OBJECT
            if _type == "integer":
                return self.gemini.protos.Type.NUMBER
            if _type == "boolean":
                return self.gemini.protos.Type.BOOLEAN
            if _type == "array":
                return self.gemini.protos.Type.ARRAY
            return self.gemini.protos.Type.TYPE_UNSPECIFIED

        return self.gemini.protos.Tool(function_declarations=[
            self.gemini.protos.FunctionDeclaration(
                name=func.get("name"),
                description=func.get("description"),
                parameters=self.gemini.protos.Schema(
                    type=_mapping_type(func.get("parameters", {}).get("type")),
                    properties={
                        param_name: self.gemini.protos.Schema(
                            type=_mapping_type(properties.get("type")),
                            description=properties.get("description")
                        )
                        for param_name, properties in \
                            func.get("parameters",{}).get("properties", {}).items()
                    },
                    required=[key for key in func.get("parameters",{}).get("properties", {}).keys()],
                )
            )
            for func in functions
        ])

    def _mapping_response_format_from_openai(self, response_format):
        if response_format.get("type") == "json_object":
            return "application/json"
        return None

    def query(self, chat_history, **kwargs):
        """
        Query the LLM model.

        Args:
            chat_history: The context (chat history).
        """
        parameters = kwargs
        chat_history = self._map_chat_history_from_openai(chat_history)

        tools = None
        if parameters.get("functions") is not None:
            tools = self._map_functions_from_openai(parameters["functions"])

        client = self.gemini.GenerativeModel(self.model)
        chat_handler = client.start_chat(history=chat_history[:-1])

        completion = chat_handler.send_message(
            chat_history[-1]["parts"],
            tools=tools,
            generation_config=self.gemini.types.GenerationConfig(
                max_output_tokens=4096,
                temperature=self.temperature,
            ),
        )

        function_outputs = {}
        for part in completion.parts:
            fn = part.function_call
            if fn:
                print("[MLE FUNC CALL]: ", fn.name)
                # avoid the multiple search function calls
                search_attempts = [item for item in self.func_call_history if item['name'] in SEARCH_FUNCTIONS]
                if len(search_attempts) > 3:
                    parameters['functions'] = None
                result = get_function(fn.name)(**dict(fn.args))
                function_outputs[fn.name] = result

        if len(function_outputs):
            response_parts = [
                self.gemini.protos.Part(
                    function_response=self.gemini.protos.FunctionResponse(
                        name=fn, response={"result": val}
                    )
                )
                for fn, val in function_outputs.items()
            ]

            completion = chat_handler.send_message(
                self.gemini.protos.Content(parts=response_parts),
                generation_config=self.gemini.types.GenerationConfig(
                    max_output_tokens=4096,
                    temperature=self.temperature,
                    response_mime_type=self._mapping_response_format_from_openai(
                        parameters.get("response_format", {})),
                ),
            )

        return completion.text

    def stream(self, chat_history, **kwargs):
        """
        Stream the output from the LLM model.
        Args:
            chat_history: The context (chat history).
        """
        client = self.gemini.GenerativeModel(self.model)
        chat_handler = client.start_chat(history=chat_history[:-1])

        completions = chat_handler.send_message(
            chat_history[-1]["parts"],
            stream=True,
            generation_config=self.gemini.types.GenerationConfig(
                max_output_tokens=4096,
                temperature=self.temperature,
            ),
        )

        for chunk in completions:
            yield chunk.text
