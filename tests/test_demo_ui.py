from src.context_budget import ContextBudgetManager
from src.demo_ui import retrieve_for_case


class FakeMemory:
    def __init__(self):
        self.calls = []
        self.budget = ContextBudgetManager(8000)

    def retrieve_long_term(self, user_id, thread_id, query):
        self.calls.append(("long_term", user_id, thread_id, query))
        return "Python preference"

    def retrieve_episodic(self, user_id, query):
        self.calls.append(("episodic", user_id, query))
        return "episode"

    def retrieve_semantic(self, graph_id, query):
        self.calls.append(("semantic", graph_id, query))
        return "Idempotency-Key policy"

    def assemble_context(self, layers):
        return self.budget.assemble(layers)


def test_ui_mixed_case_loads_thread_history_and_routes_durable_layers(monkeypatch):
    monkeypatch.setattr(
        "src.demo_ui.load_dataset",
        lambda: {
            "users": [
                {
                    "user_id": "u-1",
                    "sessions": [
                        {
                            "thread_id": "t-1",
                            "messages": [{"role": "user", "content": "base turn"}],
                        }
                    ],
                }
            ]
        },
    )
    case = {
        "id": "E07",
        "user_id": "u-1",
        "thread_id": "t-1",
        "expected_layer": "mixed",
        "query": "combine preference and policy",
    }
    memory = FakeMemory()

    result = retrieve_for_case(
        memory,
        case,
        [{"role": "user", "content": "follow-up turn"}],
    )

    assert "base turn" in result["layers"]["short_term"]
    assert "follow-up turn" in result["layers"]["short_term"]
    assert result["layers"]["long_term"] == "Python preference"
    assert result["layers"]["semantic"] == "Idempotency-Key policy"
    assert result["layers"]["episodic"] == ""
    assert [call[0] for call in memory.calls] == ["long_term", "semantic"]
    assert "<LONG_TERM>" in result["merged_context"]
    assert "<SEMANTIC>" in result["merged_context"]
    assert set(result["budget"]) == {
        "short_term",
        "long_term",
        "episodic",
        "semantic",
    }
