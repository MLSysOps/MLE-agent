class PromptChain:

    def __init__(self, prompt: str):
        """
        Initialize the prompt chain with an initial prompt string.
        :param prompt: prompt for the very first step.
        """
        self.prompt = prompt
        self.level = 0

    def get_prompt(self) -> str:
        """
        Get the current prompt.
        :return: the current prompt.
        """
        return self.prompt

    def get_level(self) -> int:
        """
        Get the current level.
        :return: the current level.
        """
        return self.level

    def set_next_prompt(self, prompt: str):
        """
        Set the next prompt in the chain.
        :param prompt: the next prompt.
        """
        self.prompt += prompt
        self.level += 1
