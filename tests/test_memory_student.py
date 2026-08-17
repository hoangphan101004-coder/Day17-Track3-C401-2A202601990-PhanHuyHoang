from types import SimpleNamespace

import pytest

from src.memory_student import StudentMemory


class FakeGraph:
    def __init__(self, *, fail_episode_scope: bool = False):
        self.calls = []
        self.fail_episode_scope = fail_episode_scope

    def search(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail_episode_scope and kwargs.get("graph_id") and kwargs["scope"] == "episodes":
            raise RuntimeError("episodes scope unavailable")
        return SimpleNamespace(episodes=[], edges=[], nodes=[])


class FakeThread:
    def __init__(self):
        self.context_calls = []

    def get_user_context(self, **kwargs):
        self.context_calls.append(kwargs)
        return SimpleNamespace(context="current user context")


class FakeClient:
    def __init__(self, *, fail_episode_scope: bool = False):
        self.graph = FakeGraph(fail_episode_scope=fail_episode_scope)
        self.thread = FakeThread()


@pytest.fixture
def disable_priming(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "src.memory_student.prime_eval_thread",
        lambda client, user_id, thread_id, query: calls.append((user_id, thread_id, query)),
    )
    return calls


def test_long_term_uses_context_block_and_user_scoped_edges(disable_priming):
    client = FakeClient()
    text = StudentMemory(client).retrieve_long_term("u-1", "t-1", "q" * 500)

    assert text == "current user context"
    assert disable_priming == [("u-1", "t-1", "q" * 500)]
    assert client.thread.context_calls == [{"thread_id": "t-1"}]
    assert client.graph.calls[0]["user_id"] == "u-1"
    assert client.graph.calls[0]["scope"] == "edges"
    assert client.graph.calls[0]["limit"] >= 20
    assert len(client.graph.calls[0]["query"]) <= 400


def test_episodic_is_user_scoped_and_caps_query():
    client = FakeClient()
    StudentMemory(client).retrieve_episodic("u-2", "word " * 200)

    call = client.graph.calls[0]
    assert call["user_id"] == "u-2"
    assert "graph_id" not in call
    assert call["scope"] == "episodes"
    assert call["limit"] >= 5
    assert len(call["query"]) <= 400


def test_semantic_uses_shared_graph_and_falls_back_to_nodes():
    client = FakeClient(fail_episode_scope=True)
    StudentMemory(client).retrieve_semantic("shared-kb", "payment retry")

    assert [call["scope"] for call in client.graph.calls] == ["episodes", "nodes"]
    assert all(call["graph_id"] == "shared-kb" for call in client.graph.calls)
    assert all("user_id" not in call for call in client.graph.calls)


def test_assemble_context_enforces_layer_priority_and_budget():
    memory = StudentMemory(FakeClient())
    merged, breakdown = memory.assemble_context(
        {
            "semantic": "semantic",
            "episodic": "episodic",
            "long_term": "long term",
            "short_term": "short term",
        }
    )

    assert merged.index("<SHORT_TERM>") < merged.index("<LONG_TERM>")
    assert merged.index("<LONG_TERM>") < merged.index("<EPISODIC>")
    assert merged.index("<EPISODIC>") < merged.index("<SEMANTIC>")
    assert set(breakdown) == {"short_term", "long_term", "episodic", "semantic"}
