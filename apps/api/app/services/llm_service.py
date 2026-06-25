import json
import os
import re
from pathlib import Path
from typing import Literal, Protocol

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.schemas.analysis import CandidateEvidence, SkillAnalysis
from app.services.paths import ROOT


LLM_TIMEOUT_SECONDS = 6.0
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


class ResumeDraftProvider(Protocol):
    def refine_resume_draft(self, skill: SkillAnalysis, template_draft: str, voice_context: str) -> str | None:
        ...


class RefinedBulletOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
        evidence = evidence_basis(skill.candidate_evidence)
        if not evidence:
            return None

        prompt = build_resume_draft_prompt(skill, template_draft, voice_context, evidence)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 120,
                "responseMimeType": "application/json",
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }
        response = httpx.post(
            url,
            params={"key": self.api_key},
            json=payload,
            timeout=LLM_TIMEOUT_SECONDS,
            trust_env=False,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Gemini request failed with status {exc.response.status_code}") from exc

        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        output = parse_bullet_json(text)
        if output is None:
            return None
        return validate_refined_bullet(output.bullet, template_draft, evidence)


def get_resume_draft_provider() -> ResumeDraftProvider | None:
    load_env_file()
    if os.environ.get("LLM_ENABLED", "false").strip().lower() not in {"1", "true", "yes", "on"}:
        return None

    provider = os.environ.get("LLM_PROVIDER", "gemini").strip().lower()
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    if not api_key or provider != "gemini":
        return None
    return GeminiFlashProvider(api_key=api_key, model=os.environ.get("LLM_MODEL"))


def evidence_basis(evidence: list[CandidateEvidence]) -> str:
    for item in evidence:
        excerpt = " ".join(item.excerpt.split())
        if excerpt and "Evidence detected in your resume" not in excerpt:
            return f"{item.source}: {excerpt}"
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
        if is_grounding_sensitive_token(token) and normalise_claim_text(token) not in allowed_text:
            return None
    return clean


def refined_by_llm() -> Literal["llm"]:
    return "llm"


def is_grounding_sensitive_token(token: str) -> bool:
    return (
        any(character.isdigit() for character in token)
        or any(character.isupper() for character in token[1:])
        or (token[:1].isupper() and token[1:].islower())
    )


def normalise_claim_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower())
