# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development

```bash
# Install in editable mode
pip install -e .

# With MLE-Bench support (Python 3.11-3.12 only)
pip install -e ".[bench]"

# Run tests
python -m unittest discover tests

# Lint (flake8 - only checks W291 trailing whitespace, max line length 256)
flake8

# Start CLI
mle <command>
```

## CLI Commands

The CLI has two entry points: `mle` and `mle-agent` (both map to `mle.cli:cli`).

- `mle new <name>` - Create new project (interactive setup for LLM provider + API keys, stores in `.mle/project.yml`)
- `mle start [baseline|report|kaggle|chat]` - Start a workflow (default: baseline)
- `mle chat [--model] [--build_mem]` - Interactive project assistant with optional RAG memory
- `mle report [repo] [--user] [--visualize]` - GitHub activity report (launches web UI by default)
- `mle report-local [path] [--email] [--start-date] [--end-date]` - Local git repo report
- `mle kaggle [--auto] [--datasets] [--description] [--submission]` - Kaggle competition workflow
- `mle integrate [--reset]` - Setup GitHub/Google Calendar/Kaggle integration
- `mle memory [--add|--rm|--update]` - Manage vector memory (LanceDB) for chat mode
- `mle traces --component <name> [--limit] [--full-output]` - View component execution traces
- `mle serve` / `mle web` - Start FastAPI backend (8000) / Next.js frontend (3000)
- `mle bench` - Experimental MLE-Bench commands (init, prepare, grade-sample)

## Architecture

### Multi-Agent System (`mle/agents/`)

Each agent wraps an LLM model with a system prompt and tool functions:
- **CodeAgent** - Generates ML project code and file structure
- **DebugAgent** - Executes code, identifies errors, iteratively fixes bugs
- **PlanAgent** - Creates structured development plans
- **AdviseAgent** - Data analysis and ML recommendations
- **ReportAgent** / **GitHubSummaryAgent** / **GitSummaryAgent** - Progress reports from GitHub/git
- **ChatAgent** - Interactive Q&A with project context

### LLM Abstraction (`mle/model/`)

Unified interface across 7 providers: OpenAI, Claude/Anthropic, Gemini, MistralAI, DeepSeek, Ollama, vLLM. All models expose `chat()` for function-calling and standard completions. `ObservableModel` wraps any model with Langfuse tracing.

### Workflow Orchestration (`mle/workflow/`)

High-level pipelines that compose agents: `baseline()`, `kaggle()`, `auto_kaggle()`, `chat()`, `report()`, `report_local()`. Uses `WorkflowCache` for checkpoint/resume of expensive steps.

### Agent Tools (`mle/function/`)

JSON-schema-defined tools agents can call: file I/O (`files.py`), code execution (`execution.py`), web/academic search (`search.py`), data preview (`data.py`), user interaction (`interaction.py`).

### Memory & RAG (`mle/utils/`)

- `LanceDBMemory` - Vector store for code embeddings (used by chat mode)
- `CodeChunker` - Tree-sitter-based code chunking with token limits
- `ComponentMemory` - Structured tracing for debugging agent runs

### Configuration

Project config lives in `.mle/project.yml` (created by `mle new`). Contains: platform, api_key, model, search_key, base_url, integration settings. Managed via `mle/utils/system.py` (`get_config()`, `write_config()`, `check_config()`).

### Web UI (`web/`)

Next.js app for report visualization. Uses Ant Design components and markdown editor. Started via `mle web` (port 3000), pairs with FastAPI backend (`mle/server/app.py`) on port 8000.

### Experimental (`exp/`)

MLE-Bench integration CLI for benchmarking. Separate entry point registered as `mle bench`.
