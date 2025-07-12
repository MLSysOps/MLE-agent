import json

from mle.function import SEARCH_FUNCTIONS, get_function, process_function_name
from mle.model.common import Model

try:
    from google.genai import client
    from google.genai import types
except ImportError:
    raise ImportError(
        "It seems you didn't install `google-genai` SDK. "
        "In order to enable the Gemini client related features, "
        "please make sure gemini Python package has been installed. "
        "More information, please refer to: https://ai.google.dev/gemini-api/docs/quickstart?lang=python"
    )

class GeminiModel(Model):

    def __init__(self, api_key, model, temperature=0.7):
        """
        Initialize the Gemini model using the `google-genai` SDK.

        Args:
            api_key (str): The Gemini API key.
            model (str): The model with version.
            temperature (float): The temperature value.
        """
        super().__init__()

        self.model = model if model else 'gemini-2.5-flash'
        self.model_type = 'Gemini'
        self.temperature = temperature
        self.client = client.Client(api_key=api_key)
        self.func_call_history = []

    def _create_gemini_tools(self, functions):
        """Converts a list of function dictionaries into a Gemini Tool object."""
        if not functions:
            return None
        
        function = []
        for func_dict in functions:
            params = func_dict.get('parameters', {})
            
            declaration = types.FunctionDeclaration(
                name=func_dict['name'],
                description=func_dict['description'],
                parameters=types.Schema(
                    type='OBJECT',
                    properties={
                        key: types.Schema(
                            type=prop.get('type', 'STRING'),
                            description=prop.get('description')
                        ) for key, prop in params.get('properties', {}).items()
                    },
                    required=list(params.get('properties', {}).keys())
                )
            )
            function.append(declaration)
        if not function:
            return None
        return [types.Tool(function_declarations=function)]

    def _adapt_history_for_gemini(self, chat_history):
        """
        Adapts mle-agent's chat history format to the one required by the Gemini API,
        separating the system instruction.
        
        Args:
            chat_history (list): The conversation history in the agent's internal format.
        
        Returns:
            tuple[str, list]: A tuple containing the system instruction and conversation history.
        """
        system_instruction = ""
        prompt = []

        for message in chat_history:
            role = message.get("role")
            content = message.get("content")

            if role == "system":
                system_instruction += content + "\n\n"
            elif role == "user" and content:
                prompt.append({'role': 'user', 'parts': [{'text': content}]})
            elif role == "assistant" and content:
                prompt.append({'role': 'model', 'parts': [{'text': content}]})

        return system_instruction.strip(), prompt

    def query(self, chat_history, **kwargs):
        """
        Query the LLM model with robust tool-calling and JSON-forcing logic.
        """
        MAX_TOOL_TURNS = 10
        SEARCH_ATTEMPT_LIMIT = 3
        self.func_call_history = []

        system_instruction, prompt = self._adapt_history_for_gemini(chat_history)
        tools = self._create_gemini_tools(kwargs.get("functions", []))

        base_config = types.GenerateContentConfig(
            tools=tools,
            temperature=self.temperature,
            system_instruction=system_instruction
        )
        json_only_config = types.GenerateContentConfig(
            temperature=self.temperature,
            response_mime_type="application/json",
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode='NONE')
            ),
            system_instruction=system_instruction
        )

        final_response_content = None
        is_final_turn = False 

        for turn in range(MAX_TOOL_TURNS):
            current_config = json_only_config if is_final_turn else base_config
            is_final_turn = False

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=current_config,
            )

            function_call = None
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        function_call = part.function_call
                        break

            if function_call:                
                prompt.append(response.candidates[0].content)
                function_name = process_function_name(function_call.name)
                arguments = dict(function_call.args)

                self.func_call_history.append(function_name)
                search_attempts = [f for f in self.func_call_history if f in SEARCH_FUNCTIONS]
                if len(search_attempts) > SEARCH_ATTEMPT_LIMIT:
                    final_response_content = f"[GEMINI WARNING]: Search function limit of {SEARCH_ATTEMPT_LIMIT} reached."
                    print(final_response_content)
                    break

                print(f"[GEMINI FUNC CALL]: Calling {function_name} with arguments: {arguments}")
                function_result = get_function(function_name)(**arguments)

                function_response_part = types.Part.from_function_response(
                    name=function_name,
                    response={"result": str(function_result)}
                )
                prompt.append(types.Content(role='tool', parts=[function_response_part]))
                
                is_final_turn = True
                continue
            else:
                final_response_content = response.text
                break

        if final_response_content is None:
            final_response_content = f"[GEMINI WARNING]: Max tool turns of {MAX_TOOL_TURNS} reached."
            print(final_response_content)

        try:
            json.loads(final_response_content)
            return final_response_content
        except (json.JSONDecodeError, TypeError) as e:
            print(f"[GEMINI ERROR]: Failed to parse final response as JSON. Error: {e}")
            return final_response_content

    def stream(self, chat_history, **kwargs):
        """
        Stream the output from the LLM model.
        Args:
            chat_history: The context (chat history).
        """
        adapted_history = self._adapt_history_for_gemini(chat_history)

        response_stream = self.client.models.generate_content_stream(
            model=self.model,
            contents=adapted_history,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                max_output_tokens=4096,
                temperature=self.temperature,
            )
        )

        for chunk in response_stream:
            yield chunk.text
