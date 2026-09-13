from app.agent.ollama_client import OllamaUnavailableError


def test_agent_chat_returns_503_when_ollama_unavailable(client, monkeypatch):
    def broken_agent_turn(db, history, message, client=None):
        raise OllamaUnavailableError("simulated failure")

    monkeypatch.setattr("app.routers.agent.run_agent_turn", broken_agent_turn)

    response = client.post("/agent/chat", json={"message": "hi", "history": []})

    assert response.status_code == 503
    body = response.json()
    assert body["error"] == "ollama_unavailable"
    assert "ollama serve" in body["detail"]
