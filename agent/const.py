DB_NAME = 'database'

CONFIG_SEC_GENERAL = 'general'
CONFIG_SEC_PROJECT = 'project'
CONFIG_SEC_API_KEY = 'api_key'
CONFIG_PROJECT_FILE = 'project.yml'
CONFIG_CHAT_HISTORY_FILE = 'project.history'
CONFIG_TASK_HISTORY_FILE = 'task.history'
CONFIG_LLM_LIST = {  # with the default model.
    'OpenAI': 'gpt-3.5-turbo',
    'Gemini': 'gemini-pro',
    'Claude': 'claude-3-opus-20240229',
    'Mistral': 'mistral-small-latest',
    'Qianfan': 'ERNIE-3.5-8K',
    'Qianwen': 'qwen-turbo'
}

# LLMs
LLM_TYPE_OPENAI = 'openai'

# Integrations
INTEGRATIOIN_AWS_S3 = 'aws_s3'
INTEGRATIOIN_HUGGINGFACE = 'huggingface'
INTEGRATIOIN_SNOWFLAKE = 'snowflake'
INTEGRATION_LIST = [
    INTEGRATIOIN_AWS_S3,
    INTEGRATIOIN_HUGGINGFACE,
    INTEGRATIOIN_SNOWFLAKE
]
