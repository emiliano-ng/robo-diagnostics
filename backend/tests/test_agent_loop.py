import json

from app.agent.ollama_client import run_agent_turn, MAX_TOOL_ITERATIONS


class FakeOllamaClient:
    """Scripted responses, popped in order — lets us fully control what
    the "model" does on each turn without needing a real Ollama server.
    Only the LLM call is faked; tool execution still hits the real
    tool functions (and real DB via fixtures) below.
    """

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def chat(self, model, messages, tools):
        self.calls += 1
        return self._responses.pop(0)


def _text_response(text):
    return {"message": {"role": "assistant", "content": text}}


def _tool_call_response(name, arguments):
    return {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"function": {"name": name, "arguments": arguments}}],
        }
    }


def test_agent_returns_immediately_when_no_tool_call_needed(db_session):
    fake = FakeOllamaClient([_text_response("Hello, how can I help?")])

    reply, history = run_agent_turn(db_session, [], "hi", client=fake)

    assert reply == "Hello, how can I help?"
    assert fake.calls == 1
    assert history[0]["role"] == "system"
    assert history[-2]["role"] == "user"
    assert history[-1]["role"] == "assistant"


def test_agent_executes_a_tool_call_then_returns_final_answer(db_session, sample_experiment):
    fake = FakeOllamaClient([
        _tool_call_response("list_experiments", {}),
        _text_response("You have 1 experiment recorded."),
    ])

    reply, history = run_agent_turn(db_session, [], "how many experiments do I have?", client=fake)

    assert reply == "You have 1 experiment recorded."
    assert fake.calls == 2
    tool_messages = [m for m in history if m.get("role") == "tool"]
    assert len(tool_messages) == 1
    parsed = json.loads(tool_messages[0]["content"])
    assert any(e["id"] == sample_experiment.id for e in parsed)


def test_agent_stops_after_max_iterations_if_model_never_finishes(db_session):
    fake = FakeOllamaClient([
        _tool_call_response("list_experiments", {}) for _ in range(MAX_TOOL_ITERATIONS + 2)
    ])

    reply, history = run_agent_turn(db_session, [], "loop forever", client=fake)

    assert "allowed steps" in reply
    assert fake.calls == MAX_TOOL_ITERATIONS


def test_agent_handles_unknown_tool_gracefully(db_session):
    fake = FakeOllamaClient([
        _tool_call_response("not_a_real_tool", {}),
        _text_response("Sorry, something went wrong."),
    ])

    reply, history = run_agent_turn(db_session, [], "do something weird", client=fake)

    tool_messages = [m for m in history if m.get("role") == "tool"]
    parsed = json.loads(tool_messages[0]["content"])
    assert "error" in parsed
    assert reply == "Sorry, something went wrong."


def test_agent_preserves_prior_conversation_history(db_session):
    fake = FakeOllamaClient([_text_response("Sure, continuing our chat.")])
    prior = [
        {"role": "system", "content": "some system prompt"},
        {"role": "user", "content": "earlier question"},
        {"role": "assistant", "content": "earlier answer"},
    ]

    reply, history = run_agent_turn(db_session, prior, "follow-up question", client=fake)

    assert history[0]["content"] == "some system prompt"
    assert sum(1 for m in history if m["role"] == "system") == 1


class FakeTypedMessage:
    """Mimics the real ollama library: response['message'] is a typed
    object with a model_dump() method, NOT a plain dict. A real bug was
    found here — appending it straight to history crashed Pydantic
    serialization on the response (history: list[dict]) since the typed
    object isn't JSON-serializable as-is.
    """

    def __init__(self, data: dict):
        self._data = data

    def model_dump(self) -> dict:
        return self._data


class FakeTypedOllamaClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def chat(self, model, messages, tools):
        self.calls += 1
        data = self._responses.pop(0)
        return {"message": FakeTypedMessage(data)}


def test_agent_converts_typed_message_object_to_plain_dict(db_session):
    # Regression test for a real bug found running against actual Ollama:
    # the client returns a pydantic-style Message object, not a dict.
    fake = FakeTypedOllamaClient([
        {"role": "assistant", "content": "Plain answer, no tools needed."}
    ])

    reply, history = run_agent_turn(db_session, [], "hi", client=fake)

    assert reply == "Plain answer, no tools needed."
    # every entry in history must be a real dict — this is what failed
    # to serialize before the fix
    assert all(isinstance(m, dict) for m in history)
