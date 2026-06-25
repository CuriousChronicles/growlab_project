import json
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.schemas.candidate import DemoCandidate
from app.schemas.job_snapshot import JobListing
from app.services.demand_counter import count_skill_demand
from app.services.entry_level_filter import tag_entry_level_listings
from app.services.evidence_classifier import classify_in_demand_skills
from app.services.skill_extractor import extract_candidate_skill_evidence, mentions_skill


def load_demo_candidate() -> DemoCandidate:
    payload = json.loads((ROOT / "data" / "demo_candidate.json").read_text(encoding="utf-8"))
    return DemoCandidate.model_validate(payload)


def load_listings() -> list[dict]:
    payload = json.loads((ROOT / "data" / "jobs_snapshot.json").read_text(encoding="utf-8"))
    raw_listings = payload["listings"] if isinstance(payload, dict) else payload
    return [JobListing.model_validate(listing).model_dump(mode="json") for listing in raw_listings]


def main() -> None:
    listings = load_listings()
    candidate = load_demo_candidate()

    pathway_listings = [
        listing
        for listing in listings
        if listing.get("pathway") == "ai_automation"
    ]
    filtered = tag_entry_level_listings(pathway_listings)
    relevant = [result.listing for result in filtered if result.relevant]

    demand = count_skill_demand(relevant)
    evidence = extract_candidate_skill_evidence(candidate)
    statuses = classify_in_demand_skills(demand, evidence)

    print("GradBridge deterministic core")
    print(f"Snapshot listings: {len(listings)}")
    print(f"ai_automation listings: {len(pathway_listings)} total -> {len(relevant)} relevant")
    print()
    print("Matcher debug")
    print(f"Relevant listings scanned: {len(relevant)}")
    for skill in ("Python", "SQL", "AWS"):
        matches = []
        for listing in relevant:
            text = f"{listing.get('title', '')} {listing.get('description', '')}"
            if mentions_skill(text, skill):
                snippet = " ".join(str(listing.get("description", "")).split())[:100]
                matches.append((listing.get("title", ""), snippet))

        print(f"{skill}: {len(matches)} matches")
        for title, snippet in matches:
            print(f"- {title}: {snippet}")
    print()
    print("Top in-demand skills")
    for item in demand[:10]:
        print(
            f"- {item.skill}: listing_count={item.listing_count}, "
            f"total_listings={item.total_listings}, employer_count={item.employer_count}, "
            f"required_count={item.required_count}"
        )

    grouped = defaultdict(list)
    for status in statuses:
        grouped[status.status].append(status)

    print()
    print("Candidate skill statuses")
    for label in ("strong_proof", "hidden_proof", "adjacent_proof", "no_proof"):
        print(f"{label}:")
        for status in grouped.get(label, []):
            sources = sorted({hit.source for hit in status.evidence})
            source_text = f" ({', '.join(sources)})" if sources else ""
            print(f"- {status.skill}{source_text}")


if __name__ == "__main__":
    main()
