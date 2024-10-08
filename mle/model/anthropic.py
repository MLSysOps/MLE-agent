import importlib.util

from mle.function import SEARCH_FUNCTIONS, get_function, process_function_name
from mle.model.common import Model


class ClaudeModel(Model):
    def __init__(self, api_key, model, temperature=0.7):
        """
        Initialize the Claude model.
        Args:
            api_key (str): The Anthropic API key.
            model (str): The model with version.
            temperature (float): The temperature value.
        """
        super().__init__()

        dependency = "anthropic"
        spec = importlib.util.find_spec(dependency)
        if spec is not None:
            self.anthropic = importlib.import_module(dependency).Anthropic
        else:
            raise ImportError(
                "It seems you didn't install anthropic. In order to enable the OpenAI client related features, "
                "please make sure openai Python package has been installed. "
                "More information, please refer to: https://docs.anthropic.com/en/api/client-sdks"
            )

        self.model = model if model else 'claude-3-5-sonnet-20240620'
        self.model_type = 'Claude'
        self.temperature = temperature
        self.client = self.anthropic(api_key=api_key)
        self.func_call_history = []

    @staticmethod
    def _add_tool_result_into_chat_history(chat_history, func, result):
        """
        Add the result of tool calls into messages.
        """
        return chat_history.extend([
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": func.id,
                        "name": func.name,
                        "input": func.input,
                    },
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": func.id,
                        "content": result,
                    },
                ]
            },
        ])

    def query(self, chat_history, **kwargs):
        """
        Query the LLM model.

        Args:
            chat_history: The context (chat history).
        """
        # claude has not system role in chat_history
        # https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts
        system_prompt = ""
        for idx, msg in enumerate(chat_history):
            if msg["role"] == "system":
                system_prompt += msg["content"]

        # claude does not support mannual `response_format`, so we append it into system prompt
        if "response_format" in kwargs.keys():
            system_prompt += (
                f"\nOutputs only valid {kwargs['response_format']['type']} without any explanatory words"
            )

        # mapping the openai function_schema to claude tool_schema
        tools = kwargs.get("functions",[])
        for tool in tools:
            if "parameters" in tool.keys():
                tool["input_schema"] = tool["parameters"]
                del tool["parameters"]

        completion = self.client.messages.create(
            max_tokens=4096,
            model=self.model,
            system=system_prompt,
            messages=[msg for msg in chat_history if msg["role"] != "system"],
            temperature=self.temperature,
            stream=False,
            tools=tools,
        )
        if completion.stop_reason == "tool_use":
            for func in completion.content:
                if func.type != "tool_use":
                    continue
                function_name = process_function_name(func.name)
                arguments = func.input
                print("[MLE FUNC CALL]: ", function_name)
                self.func_call_history.append({"name": function_name, "arguments": arguments})
                # avoid the multiple search function calls
                search_attempts = [item for item in self.func_call_history if item['name'] in SEARCH_FUNCTIONS]
                if len(search_attempts) > 3:
                    kwargs['functions'] = []
                result = get_function(function_name)(**arguments)
                self._add_tool_result_into_chat_history(chat_history, func, result)
                return self.query(chat_history, **kwargs)
        else:
            return completion.content[0].text

    def stream(self, chat_history, **kwargs):
        """
        Stream the output from the LLM model.
        Args:
            chat_history: The context (chat history).
        """
        # claude has not system role in chat_history
        # https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts
        system_prompt = ""
        for idx, msg in enumerate(chat_history):
            if msg["role"] == "system":
                system_prompt += msg["content"]
        chat_history = [msg for msg in chat_history if msg["role"] != "system"]

        # claude does not support mannual `response_format`, so we append it into system prompt
        if "response_format" in kwargs.keys():
            system_prompt += (
                f"\nOutputs only valid {kwargs['response_format']['type']} without any explanatory words"
            )

        with self.client.messages.stream(
            max_tokens=4096,
            model=self.model,
            messages=chat_history,
        ) as stream:
            for chunk in stream.text_stream:
                yield chunk
