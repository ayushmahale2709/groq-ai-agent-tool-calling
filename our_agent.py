import ast
import json
import operator
import os
import sys

from dotenv import load_dotenv
from groq import Groq
from tavily import TavilyClient

load_dotenv()

groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

MODEL = "openai/gpt-oss-120b"
MAX_STEPS = 10  # safety cap on the number of LLM <-> tool round trips


# --------------------------------------------------------------------------
# Tool 1: web search (Tavily)
# --------------------------------------------------------------------------
def web_search(query: str) -> str:
    """Search the web with Tavily and return an answer plus short sources."""
    try:
        response = tavily.search(
            query=query,
            search_depth="basic",
            max_results=5,
            include_answer=True,
        )
    except Exception as e:
        return f"Error: web search failed: {e}"

    answer = response.get("answer") or "No direct answer found."
    sources = []
    for r in response.get("results", [])[:3]:
        sources.append(f"- {r.get('title', '')}: {r.get('content', '')[:300]} ({r.get('url', '')})")

    out = f"Answer: {answer}"
    if sources:
        out += "\n\nSources:\n" + "\n".join(sources)
    return out


# --------------------------------------------------------------------------
# Tool 2: calculator (safe evaluation, no eval())
# --------------------------------------------------------------------------
_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _eval_node(node):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left, right = _eval_node(node.left), _eval_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ValueError("Exponent too large")
        return _BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("Unsupported expression")


def calculate(expression: str) -> str:
    """Evaluate a basic math expression like '2*2' or '(10+5)/3'."""
    try:
        tree = ast.parse(expression.strip().replace("^", "**"), mode="eval")
        result = _eval_node(tree)
        return str(result)
    except ZeroDivisionError:
        return "Error: division by zero"
    except Exception as e:
        return f"Error: could not evaluate '{expression}': {e}"


# --------------------------------------------------------------------------
# Tools object (standard function-calling format) + dispatch table
# --------------------------------------------------------------------------
tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for current or factual information and return an "
                "answer with sources. Use this for news, facts, prices, statistics, "
                "or anything you do not reliably know."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query, e.g. 'current population of India'",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": (
                "Evaluate a basic math expression and return the numeric result. "
                "Supports + - * / // % ** and parentheses. Example: '(12.5*4)+3'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The math expression to evaluate, e.g. '2*2'",
                    }
                },
                "required": ["expression"],
            },
        },
    },
]

available_functions = {
    "web_search": web_search,
    "calculate": calculate,
}

SYSTEM_PROMPT = (
    "You are a helpful assistant with two tools: web_search and calculate.\n"
    "- Use web_search for facts, news, or anything that needs up-to-date information.\n"
    "- Use calculate for any arithmetic; do not do maths in your head.\n"
    "- If a question needs several steps (for example, search for a number and then "
    "do maths on it), call ONE tool at a time and use each result before deciding "
    "the next step.\n"
    "- Only give the final answer once you have everything you need.\n"
    "- If no tool is needed, answer directly."
)


# --------------------------------------------------------------------------
# Agent loop
# --------------------------------------------------------------------------
def run_agent(user_query: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]

    for step in range(1, MAX_STEPS + 1):
        response = groq.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        msg = response.choices[0].message

        # No tool call -> the model has its final answer
        if not msg.tool_calls:
            return msg.content or ""

        # Record the assistant's tool-call message in the history
        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            }
        )

        # Run each requested tool and feed the result back
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}

            print(f"[step {step}] calling {name}({args})")

            func = available_functions.get(name)
            if func is None:
                result = f"Error: unknown tool '{name}'"
            else:
                try:
                    result = func(**args)
                except TypeError as e:
                    result = f"Error: bad arguments for {name}: {e}"

            print(f"[step {step}] result: {result[:200]}")

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": name,
                    "content": str(result),
                }
            )

    return "Sorry, I couldn't finish within the allowed number of steps."


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or input("Ask me anything: ")
    print("\nFinal answer:\n" + run_agent(query))