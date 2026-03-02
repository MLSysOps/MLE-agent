# MLE-agent LazyLLM Integration

This document describes how to use LazyLLM integration in MLE-agent for unified LLM provider support.

## 🎯 What is LazyLLM?

[LazyLLM](https://github.com/LazyAGI/LazyLLM) is a low-code development tool for building multi-Agent LLM applications. Its core feature is **unifying interfaces across different LLM providers**.

### Supported Providers

**Online Models (Cloud APIs):**
- International: OpenAI, Anthropic, Gemini, Mistral, DeepSeek
- Chinese: Qwen (通义), Zhipu GLM (智谱), Kimi, MiniMax, Doubao (豆包), etc.
- And 20+ more providers...

**Local Models (Self-hosted):**
- vLLM, LMDeploy, Ollama
- Automatic model download and deployment
- Support for fine-tuning

## 📦 Installation

Install LazyLLM as an optional dependency:

```bash
pip install lazyllm
# or
uv pip install lazyllm
```

## ⚙️ Configuration

### Option 1: Project Configuration File

Edit `.mle/project.yml`:

```yaml
platform: LazyLLM
model: deepseek-chat  # or qwen-plus, gpt-4o, etc.
source: deepseek      # optional: auto-detected from model name
api_key: your-api-key # optional: can use environment variable
temperature: 0.7
base_url: null        # optional: custom endpoint
```

### Option 2: Environment Variables (MLE_ Namespace)

LazyLLM integration uses the `MLE_` namespace prefix for API keys:

```bash
export MLE_DEEPSEEK_API_KEY=your-deepseek-api-key
export MLE_QWEN_API_KEY=your-qwen-api-key
export MLE_OPENAI_API_KEY=your-openai-api-key
```

Then configure `.mle/project.yml`:

```yaml
platform: LazyLLM
model: deepseek-chat
# API key will be loaded from MLE_DEEPSEEK_API_KEY env var
```

## 🚀 Usage Examples

### Example 1: Using DeepSeek

```python
from mle.model import load_model

# Configure project
# .mle/project.yml:
#   platform: LazyLLM
#   model: deepseek-chat

model = load_model(project_dir='/path/to/project')
response = model.query([
    {"role": "user", "content": "Hello!"}
])
```

### Example 2: Switching Providers

Just change the model name in config - no code changes needed!

```yaml
# Switch from DeepSeek to Qwen
platform: LazyLLM
model: qwen-plus
source: qwen
```

### Example 3: Using Local Models

```yaml
# Use local model with vLLM
platform: LazyLLM
model: internlm2-chat-7b
# LazyLLM will automatically use local deployment
```

## 🔑 API Key Management

### Priority Order

1. Explicit `api_key` in `.mle/project.yml`
2. `MLE_<SOURCE>_API_KEY` environment variable
3. `<SOURCE>_API_KEY` environment variable (fallback)
4. Common default keys (e.g., `OPENAI_API_KEY`)

### Supported API Key Variables

```bash
# Chinese providers
export MLE_DEEPSEEK_API_KEY=sk-xxx
export MLE_QWEN_API_KEY=sk-xxx
export MLE_GLM_API_KEY=xxx
export MLE_KIMI_API_KEY=xxx
export MLE_MINIMAX_API_KEY=xxx
export MLE_DOUBAO_API_KEY=xxx

# International providers
export MLE_OPENAI_API_KEY=sk-xxx
export MLE_ANTHROPIC_API_KEY=sk-ant-xxx
export MLE_GEMINI_API_KEY=xxx
```

## 💡 Benefits

1. **Unified Interface**: One code path for 20+ providers
2. **Easy Switching**: Change providers by config, not code
3. **Auto-Detection**: LazyLLM AutoModel selects best option
4. **Local + Cloud**: Seamless fallback between local and cloud models
5. **Fine-tuning**: Access to LazyLLM's fine-tuning capabilities

## 🧪 Testing

Run the test suite:

```bash
cd MLE-agent
python tests/test_lazyllm.py
```

The test suite covers:
- DeepSeek integration
- Qwen integration
- Streaming mode
- Environment variable loading

## 📝 Migration Guide

### From Existing Provider to LazyLLM

**Before (OpenAI):**
```yaml
platform: OpenAI
model: gpt-4o
api_key: sk-xxx
```

**After (LazyLLM with OpenAI):**
```yaml
platform: LazyLLM
model: gpt-4o
# Uses MLE_OPENAI_API_KEY env var
```

**Or switch to DeepSeek:**
```yaml
platform: LazyLLM
model: deepseek-chat
# Uses MLE_DEEPSEEK_API_KEY env var
```

## 🔗 References

- LazyLLM GitHub: https://github.com/LazyAGI/LazyLLM
- LazyLLM Docs: https://docs.lazyllm.ai/
- MLE-agent Issue: https://github.com/MLSysOps/MLE-agent/issues/324

## 🤝 Contributing

Found a bug or want to add more providers? Please open an issue or submit a PR!
