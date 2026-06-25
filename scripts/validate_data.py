from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError


ROOT_DIR = Path(__file__).resolve().parents[1]
API_DIR = ROOT_DIR / "apps" / "api"
sys.path.insert(0, str(API_DIR))

from app.schemas.candidate import DemoCandidate  # noqa: E402
from app.schemas.job_snapshot import JobSnapshot  # noqa: E402


VALIDATION_TARGETS = [
    (ROOT_DIR / "data" / "jobs_snapshot.json", JobSnapshot),
    (ROOT_DIR / "data" / "demo_candidate.json", DemoCandidate),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_file(path: Path, schema: type) -> bool:
    try:
        schema.model_validate(load_json(path))
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"{path.relative_to(ROOT_DIR)}: validation failed")
        print(exc)
        return False

    print(f"{path.relative_to(ROOT_DIR)}: OK")
    return True


def main() -> int:
    ok = True
    for path, schema in VALIDATION_TARGETS:
        ok = validate_file(path, schema) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
