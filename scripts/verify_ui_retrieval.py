"""Live smoke check for the Streamlit demo's retrieval wiring."""

from src.demo_ui import load_cases, retrieve_for_case
from src.memory_student import StudentMemory
from src.zep_common import get_zep_client


def main() -> None:
    case = next(item for item in load_cases() if item["id"] == "E07")
    result = retrieve_for_case(StudentMemory(get_zep_client()), case, [])
    merged = result["merged_context"]
    assert "Python" in merged
    assert "Idempotency-Key" in merged

    active = [name for name, value in result["layers"].items() if value.strip()]
    used_tokens = sum(item["used_tokens"] for item in result["budget"].values())
    print("UI retrieval E07 PASS")
    print(f"active_layers={','.join(active)}")
    print(f"merged_tokens={used_tokens}")


if __name__ == "__main__":
    main()
