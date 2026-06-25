import json
import os
import re
from hashlib import sha256
from pathlib import Path
from time import sleep
from typing import Protocol

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.schemas.analysis import CandidateEvidence, SkillAnalysis
from app.services.paths import DATA_DIR, ROOT


LLM_TIMEOUT_SECONDS = 24.0
LLM_REQUEST_TIMEOUT_SECONDS = 10.0
LLM_MAX_ATTEMPTS = 2
TRANSIENT_GEMINI_STATUSES = {429, 500, 502, 503, 504}
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
LLM_CACHE_PATH = DATA_DIR / "llm_cache.json"


class ResumeDraftProvider(Protocol):
    def refine_resume_draft(self, skill: SkillAnalysis, template_draft: str, voice_context: str) -> str | None:
        ...


class RefinedBulletOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bullet: str = Field(min_length=1, max_length=180)


class CachedBullet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill: str
    evidence_excerpt: str
    bullet: str = Field(min_length=1, max_length=180)


def load_env_file(path: Path | None = None) -> None:
    env_path = path or ROOT / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


class GeminiFlashProvider:
    def __init__(self, api_key: str, model: str | None = None) -> None:
        self.api_key = api_key
        self.model = model or DEFAULT_GEMINI_MODEL

    def refine_resume_draft(self, skill: SkillAnalysis, template_draft: str, voice_context: str) -> str | None:
        evidence = evidence_excerpt(skill.candidate_evidence)
        if not evidence:
            return None

        cached = read_cached_refinement(skill.name, evidence, template_draft)
        if cached:
            return cached

        prompt = build_resume_draft_prompt(skill, template_draft, voice_context, evidence)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 120,
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "bullet": {
                            "type": "STRING",
                            "description": "One concise grounded resume bullet, about 25 words or fewer.",
                        }
                    },
                    "required": ["bullet"],
                    "propertyOrdering": ["bullet"],
                },
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }
        for attempt in range(LLM_MAX_ATTEMPTS):
            response = post_gemini_json(url, self.api_key, payload)
            if response is None:
                sleep_before_retry(attempt)
                continue

            try:
                text = response["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError, TypeError):
                sleep_before_retry(attempt)
                continue
            output = parse_bullet_json(text)
            if output is None:
                sleep_before_retry(attempt)
                continue

            refined = validate_refined_bullet(output.bullet, template_draft, evidence)
            if refined:
                write_cached_refinement(skill.name, evidence, refined)
                return refined
            sleep_before_retry(attempt)
        return None


def get_resume_draft_provider() -> ResumeDraftProvider | None:
    load_env_file()
    if os.environ.get("LLM_ENABLED", "false").strip().lower() not in {"1", "true", "yes", "on"}:
        return None

    provider = os.environ.get("LLM_PROVIDER", "gemini").strip().lower()
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    if not api_key or provider != "gemini":
        return None
    return GeminiFlashProvider(api_key=api_key, model=os.environ.get("LLM_MODEL"))


def post_gemini_json(url: str, api_key: str, payload: dict) -> dict | None:
    try:
        response = httpx.post(
            url,
            params={"key": api_key},
            json=payload,
            timeout=LLM_REQUEST_TIMEOUT_SECONDS,
            trust_env=False,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in TRANSIENT_GEMINI_STATUSES:
            return None
        raise RuntimeError(f"Gemini request failed with status {exc.response.status_code}") from exc
    except (httpx.RequestError, KeyError, IndexError, TypeError, ValueError):
        return None


def sleep_before_retry(attempt: int) -> None:
    if attempt < LLM_MAX_ATTEMPTS - 1:
        sleep(0.35)


def evidence_excerpt(evidence: list[CandidateEvidence]) -> str:
    for item in evidence:
        excerpt = " ".join(item.excerpt.split())
        if excerpt and "Evidence detected in your resume" not in excerpt:
            return excerpt
    return ""


def build_resume_draft_prompt(skill: SkillAnalysis, template_draft: str, voice_context: str, evidence: str) -> str:
    return (
        "Rewrite one resume bullet in the candidate's own plain technical voice.\n"
        "Use ONLY the evidence excerpt below as the factual basis.\n"
        "Never invent experience, tools, metrics, employers, awards, responsibilities, or outcomes.\n"
        "Candidate voice examples are for style only; do not use them as facts.\n"
        "Return one bullet, about 25 words or fewer, as JSON only.\n\n"
        f"Skill: {skill.name}\n"
        f"Evidence excerpt, sole factual basis: {evidence}\n"
        f"Template bullet to rewrite: {template_draft}\n"
        f"Candidate voice/style examples:\n{voice_context or evidence}\n\n"
        'Return exactly this JSON shape: {"bullet": "one concise resume bullet"}'
    )


def parse_bullet_json(text: str) -> RefinedBulletOutput | None:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return RefinedBulletOutput.model_validate(json.loads(stripped))
    except (json.JSONDecodeError, TypeError, ValidationError):
        return None


def cache_key(skill_name: str, evidence: str) -> str:
    payload = json.dumps(
        {"skill": skill_name.strip(), "evidence_excerpt": " ".join(evidence.split())},
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def read_llm_cache(path: Path | None = None) -> dict[str, dict]:
    cache_path = path or LLM_CACHE_PATH
    if not cache_path.exists():
        return {}
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def write_llm_cache(cache: dict[str, dict], path: Path | None = None) -> None:
    cache_path = path or LLM_CACHE_PATH
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = cache_path.with_suffix(f"{cache_path.suffix}.tmp")
    temp_path.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")
    temp_path.replace(cache_path)


def read_cached_refinement(skill_name: str, evidence: str, template_draft: str) -> str | None:
    cache = read_llm_cache()
    raw = cache.get(cache_key(skill_name, evidence))
    if not isinstance(raw, dict):
        return None
    try:
        cached = CachedBullet.model_validate(raw)
    except ValidationError:
        return None
    if cached.skill != skill_name or cached.evidence_excerpt != evidence:
        return None
    return validate_refined_bullet(cached.bullet, template_draft, evidence)


def write_cached_refinement(skill_name: str, evidence: str, bullet: str) -> None:
    cache = read_llm_cache()
    cache[cache_key(skill_name, evidence)] = CachedBullet(
        skill=skill_name,
        evidence_excerpt=evidence,
        bullet=bullet,
    ).model_dump()
    try:
        write_llm_cache(cache)
    except OSError:
        return


def validate_refined_bullet(bullet: str, template_draft: str, allowed_context: str = "") -> str | None:
    clean = " ".join(bullet.replace("\n", " ").split()).strip(" -")
    if not clean or len(clean.split()) > 28 or len(clean) > 180:
        return None
    if clean == template_draft:
        return None
    if any(marker in clean.lower() for marker in [" as an ai ", "i don't", "cannot", "unknown"]):
        return None
    allowed_text = normalise_claim_text(allowed_context)
    for index, token in enumerate(re.findall(r"\b[A-Za-z][A-Za-z0-9.+#/-]*\b", clean)):
        if index == 0 and token[:1].isupper() and token[1:].islower():
            continue
        if is_grounding_sensitive_token(token) and not token_is_grounded(token, allowed_text):
            return None
    return clean


def refined_by_llm(provider: ResumeDraftProvider) -> str:
    return str(getattr(provider, "model", "llm"))


def is_grounding_sensitive_token(token: str) -> bool:
    return (
        any(character.isdigit() for character in token)
        or any(character.isupper() for character in token[1:])
        or (token[:1].isupper() and token[1:].islower())
    )


def token_is_grounded(token: str, allowed_text: str) -> bool:
    normalised = normalise_claim_text(token)
    if normalised in allowed_text:
        return True
    if normalised in {"pr", "prs"} and "pull request" in allowed_text:
        return True
    return False


def normalise_claim_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower())