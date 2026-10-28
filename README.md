# Groq AI Agent with Tool Calling

A simple AI agent built with Python and Groq that can intelligently choose between two tools: **web search using Tavily** and **mathematical calculations using Python**.

This project demonstrates how an LLM can go beyond generating text by selecting and executing external tools based on a user's query.

## Features

- **LLM-powered tool selection:** Uses Groq to decide which tool is appropriate for a query.
- **Web Search:** Uses the Tavily API to retrieve information from the web.
- **Calculator:** Performs basic mathematical operations using Python.
- **Automatic Tool Calling:** The LLM selects the tool and supplies its required arguments.
- **Iterative Execution:** Supports multiple tool calls through an execution loop.
- **Execution Limit:** Uses a maximum step limit to prevent endless tool-calling loops.
- **Environment Variables:** Stores API keys in a `.env` file.

## Tech Stack

- Python
- Groq API
- Tavily Search API
- python-dotenv

## Architecture

```text
              User Query
                   |
                   v
              Groq LLM
                   |
                   v
             Tool Selection
                   |
            +------+------+
            |             |
            v             v
      Python Calculator  Tavily Web Search
            |             |
            +------+------+
                   |
                   v
              Tool Results
                   |
                   v
               Groq LLM
                   |
                   v
              Final Answer
```

## Project Structure

```text
groq-ai-agent-tool-calling/
├── agent.py
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/groq-ai-agent-tool-calling.git
cd groq-ai-agent-tool-calling
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

On macOS or Linux:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Replace the placeholders with your own API keys.

### 5. Run the agent

```bash
python agent.py
```

Enter a query and let the agent select the appropriate tool.

## Example Queries

**Mathematical calculation**

```text
What is 394 multiplied by 11?
```

Expected result: `4334`

**Web search**

```text
What are the latest developments in AI?
```

The agent uses Tavily to search for relevant web information.

**Multi-step query**

```text
Find India's current Prime Minister, calculate the number of days until 1 January 2027, and multiply that number by 394.
```

This type of query can demonstrate sequential tool usage if supported by the agent's execution loop.

## How It Works

1. The user submits a natural-language query.
2. The Groq LLM evaluates the query and selects an appropriate tool.
3. The Python application executes the selected function.
4. The tool result is returned to the LLM.
5. The LLM generates the final response.
6. The process continues as needed, subject to the configured execution limit.

## Security

- Never commit your `.env` file or expose API keys.
- Add `.env` and virtual environment folders to `.gitignore`.
- Validate calculator expressions and avoid unrestricted `eval()` execution.

Example `.gitignore`:

```gitignore
.env
venv/
__pycache__/
*.pyc
```

## Learning Outcomes

Through this project, I explored:

- LLM tool calling and function execution
- Automatic tool selection
- Integrating external APIs with Python
- Iterative agent execution
- Basic execution limits and error prevention
- The role of tools in building AI agents

## Future Improvements

- Add more tools, such as a unit converter or database search.
- Improve error handling and API failure recovery.
- Add structured logging and tool-call tracing.
- Build a simple web interface using FastAPI or Streamlit.
- Add automated tests for the calculator and agent loop.

## Author

**Ayush Mahale**

GitHub: [ayushmahale2709](https://github.com/ayushmahale2709)

Portfolio: [View Portfolio](https://ayushmahale2709.github.io/ayush-portfolio/)

---

*Built as a learning project while exploring LLMs, tool calling, and AI agents.*
