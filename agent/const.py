CONFIG_SEC_GENERAL = 'general'
CONFIG_SEC_API_KEY = 'api_key'
CONFIG_LLM_LIST = {  # with the default model.
    'OpenAI': 'gpt-3.5-turbo',
    'Gemini': 'gemini-pro',
    'Claude': 'claude-3-opus-20240229',
    'Mistral': 'mistral-small-latest',
    'Qianfan': 'ERNIE-3.5-8K',
    'Qianwen': 'qwen-turbo'
}

COMMAND_HISTORY_COUNT = 15
DB_PATH = 'database'
DB_COMMAND_HISTORY = 'history'
DB_SYS_METRICS = 'system'

# LLMs
CONFIG_SEC_OPENAI = 'openai'
CONFIG_SEC_GEMINI = 'gemini'
CONFIG_SEC_CLAUDE = 'claude'
CONFIG_SEC_MISTRAL = 'mistral'
CONFIG_SEC_QIANFAN = 'qianfan'
CONFIG_SEC_QIANWEN = 'qianwen'

# Plugins
PLUGIN_SHELL_ZSH = 'zsh'
PLUGIN_SHELL_BASH = 'bash'
PLUGIN_SHELL_FISH = 'fish'


PLUGIN_LIST = [PLUGIN_SHELL_ZSH, PLUGIN_SHELL_BASH, PLUGIN_SHELL_FISH]
