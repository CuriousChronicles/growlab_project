import sys
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def disable_llm_api_key(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "")


API_DIR = Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))
