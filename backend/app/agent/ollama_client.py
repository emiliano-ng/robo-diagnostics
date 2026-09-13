"""Tool-calling loop against a local Ollama instance.

NOTE: this module talks to a real Ollama server and hasn't been
exercised end-to-end in the development sandbox (no local GPU/Ollama
there) — it's built carefully against Ollama's documented tool-calling
API and unit-tested with a mocked client (see tests/test_agent_loop.py),
but run it against your actual local Ollama before trusting it blindly.
"""

import os
import json
import logging

from ollama import Client

from app.agent.tools import TOOL_SCHEMAS, TOOL_FUNCTIONS

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "90"))

SYSTEM_PROMPT = (
    "You are a diagnostics assistant for a robotics experiment platform. "
    "Answer questions about experiments, runs, and SLAM degradation "
    "analysis by calling the tools available to you. Always call a tool "
    "to look up real data rather than guessing numbers. When comparing "
    "runs, call get_diagnostics_summary (calling analyze_run first if "
    "it reports analyzed=false) for each run separately, then compare "
    "the results yourself in your answer — the tools don't do the "
    "comparison for you."
)

# Guards against a model that keeps requesting tools indefinitely (e.g.
# stuck in a loop, or repeatedly calling a tool with bad arguments) —
# without this, a single confused turn could hang the request forever.
MAX_TOOL_ITERATIONS = 6


class OllamaUnavailableError(Exception):
    """Raised when the local Ollama server can't be reached, or times
    out — distinct from a bug in our own code, so it gets a clear 503
    with an actionable message instead of a generic 500. This is the
    difference between "the agent is broken" and "Ollama isn't running",
    which matters most exactly when it happens live during a demo.
    """


def _execute_tool_call(db, name: str, arguments: dict) -> dict:
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return func(db, **arguments)
    except TypeError as e:
        return {"error": f"Invalid arguments for {name}: {e}"}
    except Exception:
        logger.exception("Tool %s failed", name)
        return {"error": f"Tool {name} raised an unexpected error"}


def run_agent_turn(
    db, conversation: list[dict], user_message: str, client: Client | None = None
) -> tuple[str, list[dict]]:
    """Runs one user turn through the tool-calling loop.

    Returns (final_reply_text, updated_conversation). `conversation` is
    the prior message history *without* the new user message — the
    caller persists the returned history and passes it back on the next
    call. This function itself holds no state between calls, so it's
    safe to run behind a stateless HTTP endpoint.

    `client` is injectable for testing (a mocked Ollama client); in
    production it defaults to a real client pointed at OLLAMA_BASE_URL.
    """
    if client is None:
        client = Client(host=OLLAMA_BASE_URL, timeout=OLLAMA_TIMEOUT_SECONDS)

    messages = list(conversation)
    if not messages or messages[0].get("role") != "system":
        messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
    messages.append({"role": "user", "content": user_message})

    for _ in range(MAX_TOOL_ITERATIONS):
        try:
            response = client.chat(model=OLLAMA_MODEL, messages=messages, tools=TOOL_SCHEMAS)
        except Exception as e:
            # Only the network/model call is wrapped here — tool
            # execution errors are already handled inside
            # _execute_tool_call and returned as normal tool results, so
            # they never get misclassified as "Ollama is unreachable".
            logger.error("Failed to reach Ollama at %s: %s", OLLAMA_BASE_URL, e)
            raise OllamaUnavailableError(
                f"Could not reach Ollama at {OLLAMA_BASE_URL}. Is it running?"
            ) from e

        message = response["message"]

        # The ollama client returns a typed Message object here, not a
        # plain dict — convert it so the history stays JSON-serializable
        # (our response model expects list[dict]) and round-trips
        # cleanly as input on the next call. Handles both the real
        # client (pydantic model, has model_dump) and simple dict-based
        # fakes used in tests.
        message_dict = message.model_dump() if hasattr(message, "model_dump") else dict(message)
        messages.append(message_dict)

        tool_calls = message_dict.get("tool_calls")
        if not tool_calls:
            return message_dict.get("content", ""), messages

        for call in tool_calls:
            name = call["function"]["name"]
            arguments = call["function"].get("arguments", {}) or {}
            result = _execute_tool_call(db, name, arguments)
            messages.append({
                "role": "tool",
                "content": json.dumps(result),
                "name": name,
            })

    return (
        "I wasn't able to finish reasoning about that within the allowed "
        "steps — try asking a more specific question.",
        messages,
    )
