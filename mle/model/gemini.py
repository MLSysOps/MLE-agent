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

        dependency = "google"
        spec = importlib.util.find_spec(dependency)
        if spec is not None:
            self.gemini = importlib.import_module(dependency).generativeai
        else:
            raise ImportError(
                "It seems you didn't install `google-generativeai`. "
                "In order to enable the Gemini client related features, "
                "please make sure gemini Python package has been installed. "
                "More information, please refer to: https://ai.google.dev/gemini-api/docs/quickstart?lang=python"
            )

        self.model = model if model else 'gemini-1.5-flash-002'
        self.model_type = 'Gemini'
        self.temperature = temperature
        self.func_call_history = []

    @staticmethod
    def _map_roles_from_openai(chat_history):
        _map_dict = {
            "system": "model",
            "user": "user",
            "assistant": "model",
            "content": "parts",
        }
        return dict({_map_dict[k]: v for k, v in chat_history.items()})

    def query(self, chat_history, **kwargs):
        """
        Query the LLM model.

        Args:
            chat_history: The context (chat history).
        """
        parameters = kwargs

        tools = None
        if parameters.get("functions") is not None:
            tools = {'function_declarations': parameters["functions"]}
            self.gemini.protos.Tool(tools)

        client = self.gemini.GenerativeModel(self.model, tools=tools)
        chat_handler = client.start_chat(history=chat_history[:-1])
        generation_config = self.gemini.types.GenerationConfig(
            max_output_tokens=4096,
            temperature=self.temperature,
            response_mime_type='application/json' \
                if parameters.get("response_format") == {'type': 'json_object'} else None,
        )

        completion = chat_handler.send_message(
            chat_history[-1]["parts"],
            generation_config=generation_config,
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
                result = get_function(fn.name)(**fn.args)
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
                response_parts,
                generation_config=generation_config,
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
        generation_config = self.gemini.types.GenerationConfig(
            max_output_tokens=4096,
            temperature=self.temperature,
        )

        completions = chat_handler.send_message(
            chat_history[-1]["parts"],
            generation_config=generation_config,
            stream=True
        )

        for chunk in completions:
            yield chunk.text
