## 📋 Prerequisites

- Python 3.8+
- OpenAI API key
- Internet connection for research APIs

## 🔧 Installation

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up OpenAI API Key** (Optional - can be done at runtime)
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

## 🎯 Quick Start

### Method 1: Interactive Mode

```bash
python main.py
```

The script will:

1. Prompt for OpenAI API key (if not in environment)
2. Ask for target directory for solution files
3. Start solving the default MNIST problem

### Method 2: Command Line with Directory

```bash
python main.py /path/to/solution/directory
```

## 🤖 How It Works

The system uses three specialized agents in sequence:

### 1. 🔍 Advisor Agent

- Searches arXiv for relevant research papers
- Queries Papers with Code for implementations
- Summarizes findings and state-of-the-art approaches

### 2. 📋 Planner Agent

- Analyzes research findings
- Creates detailed implementation plan
- Specifies data preprocessing, model architecture, and evaluation strategy

### 3. 💻 Developer Agent

- Generates complete Python code based on the plan
- Creates project structure using `mkdir`, `write_file`, `read_file`
- Implements data handling, model training, and submission format