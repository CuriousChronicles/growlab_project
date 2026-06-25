from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


ADZUNA_URL = "https://api.adzuna.com/v1/api/jobs/nz/search/1"
ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / ".env"
OUTPUT_PATH = ROOT_DIR / "data" / "jobs_snapshot.json"

PATHWAYS = {
    "ai_automation": "python automation",
    "software_fullstack": "graduate developer",
    "embedded_firmware": "embedded firmware",
}

def load_env(path: Path) -> None:
    if not path.exists():
        print(f"Missing .env file at {path}", file=sys.stderr)
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def require_credentials() -> tuple[str, str] | None:
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    missing = [name for name, value in (("ADZUNA_APP_ID", app_id), ("ADZUNA_APP_KEY", app_key)) if not value]
    if missing:
        print(f"Missing required Adzuna credential(s): {', '.join(missing)}", file=sys.stderr)
        print("Add them to .env, then run this script again.", file=sys.stderr)
        return None
    return app_id, app_key


def fetch_pathway(pathway: str, keywords: str, app_id: str, app_key: str) -> list[dict[str, Any]]:
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what_or": keywords,
        "where": "New Zealand",
        "results_per_page": 50,
        "max_days_old": 30,
        "content-type": "application/json",
    }
    url = f"{ADZUNA_URL}?{urlencode(params)}"

    try:
        with urlopen(url, timeout=30) as response:
            status = getattr(response, "status", 200)
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        print(f"{pathway}: Adzuna returned HTTP {exc.code}: {message}", file=sys.stderr)
        return []
    except URLError as exc:
        print(f"{pathway}: Could not reach Adzuna: {exc.reason}", file=sys.stderr)
        return []
    except TimeoutError:
        print(f"{pathway}: Timed out while contacting Adzuna.", file=sys.stderr)
        return []

    if status != 200:
        print(f"{pathway}: Adzuna returned HTTP {status}.", file=sys.stderr)
        return []

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        print(f"{pathway}: Could not parse Adzuna response as JSON: {exc}", file=sys.stderr)
        return []

    results = payload.get("results")
    if not isinstance(results, list):
        print(f"{pathway}: Response did not include a results list.", file=sys.stderr)
        return []
    if not results:
        print(f"{pathway}: Adzuna returned no listings.")
        return []

    return results


def display_name(value: Any) -> str:
    if isinstance(value, dict):
        display = value.get("display_name")
        return str(display).strip() if display else ""
    return ""


def keep_fields(job: dict[str, Any], pathway: str) -> dict[str, str]:
    return {
        "title": str(job.get("title") or "").strip(),
        "company": display_name(job.get("company")),
        "location": display_name(job.get("location")),
        "description": str(job.get("description") or "").strip(),
        "created": str(job.get("created") or "").strip(),
        "redirect_url": str(job.get("redirect_url") or "").strip(),
        "pathway": pathway,
    }


def normalized_key(job: dict[str, str]) -> str:
    parts = (job["company"], job["title"], job["location"])
    return "|".join(" ".join(part.lower().split()) for part in parts)


def capture() -> int:
    load_env(ENV_PATH)
    credentials = require_credentials()
    if credentials is None:
        return 1

    app_id, app_key = credentials
    listings: list[dict[str, str]] = []
    seen: set[str] = set()
    per_pathway = dict.fromkeys(PATHWAYS, 0)

    for index, (pathway, keywords) in enumerate(PATHWAYS.items()):
        if index:
            time.sleep(1.0)

        raw_jobs = fetch_pathway(pathway, keywords, app_id, app_key)
        for raw_job in raw_jobs:
            if not isinstance(raw_job, dict):
                continue

            job = keep_fields(raw_job, pathway)
            key = normalized_key(job)
            if not key or key in seen:
                continue

            seen.add(key)
            listings.append(job)
            per_pathway[pathway] += 1

    if not listings:
        print("No listings captured. Existing snapshot was not overwritten.", file=sys.stderr)
        return 1

    snapshot = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source": "Adzuna NZ",
        "location": "Auckland",
        "listings": listings,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for pathway, count in per_pathway.items():
        print(f"{pathway}: {count} listings")
    print(f"total: {len(listings)} listings")
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(capture())
