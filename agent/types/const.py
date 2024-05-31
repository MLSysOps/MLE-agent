# Main
CODE_LANGUAGE = 'python'
# Configurations
CONFIG_SEC_GENERAL = 'general'
CONFIG_SEC_PROJECT = 'project'
CONFIG_SEC_API_KEY = 'api_key'
CONFIG_PROJECT_FILE = 'project.yml'
CONFIG_CHAT_HISTORY_FILE = 'project.history'
CONFIG_TASK_HISTORY_FILE = 'task.history'

# Database
DB_NAME = 'database'
TABLE_PROJECTS = 'projects.json'

# LLMs
LLM_TYPE_OPENAI = 'openai'
LLM_TYPE_OLLAMA = 'ollama'

# Search Engine
SEARCH_ENGINE_GOOGLE = 'google'
SEARCH_ENGINE_SEARCHAPI = 'searchapi'
SEARCH_ENGINE_BING = 'bing'

# Integrations
INTEGRATIOIN_AWS_S3 = 'aws_s3'
INTEGRATIOIN_HUGGINGFACE = 'huggingface'
INTEGRATIOIN_SNOWFLAKE = 'snowflake'
INTEGRATION_LIST = [
    INTEGRATIOIN_AWS_S3,
    INTEGRATIOIN_HUGGINGFACE,
    INTEGRATIOIN_SNOWFLAKE
]
