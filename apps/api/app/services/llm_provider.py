import json
import os
import re
from pathlib import Path
from typing import Protocol

import httpx

from app.schemas.analysis import CandidateEvidence, SkillAnalysis
from app.services.paths import ROOT


LLM_TIMEOUT_SECONDS = 5.0
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"


class ResumeDraftProvider(Protocol):
    def refine_resume_draft(self, skill: SkillAnalysis, template_draft: str, voice_context: str) -> str | None:
        ...


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
        prompt = build_resume_draft_prompt(skill, template_draft, voice_context)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 180,
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
        bullet = parse_bullet_json(text).get("bullet")
        if not isinstance(bullet, str):
            return None
        return validate_refined_bullet(bullet, template_draft, f"{voice_context}\n{build_voice_context(skill.candidate_evidence)}")


def get_resume_draft_provider() -> ResumeDraftProvider | None:
    load_env_file()
    provider = os.environ.get("LLM_PROVIDER", "gemini").strip().lower()
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    if not api_key or provider != "gemini":
        return None
    return GeminiFlashProvider(api_key=api_key, model=os.environ.get("LLM_MODEL"))


def build_voice_context(evidence: list[CandidateEvidence]) -> str:
    return "\n".join(f"- {item.source}: {item.excerpt}" for item in evidence[:3])


def build_resume_draft_prompt(skill: SkillAnalysis, template_draft: str, voice_context: str) -> str:
    evidence_context = build_voice_context(skill.candidate_evidence)
    return (
        "Rewrite one resume bullet in the candidate's own plain technical voice.\n"
        "Ground the wording ONLY in the provided evidence and existing template.\n"
        "Do not invent metrics, outcomes, tools, employers, awards, or responsibilities.\n"
        "Keep the same factual claims as the template, and return JSON only.\n\n"
        f"Skill: {skill.name}\n"
        f"Existing template bullet: {template_draft}\n\n"
        f"Candidate voice examples:\n{voice_context or evidence_context}\n\n"
        f"Allowed evidence:\n{evidence_context}\n\n"
        'Return exactly: {"bullet": "one concise resume bullet"}'
    )


def parse_bullet_json(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    return json.loads(stripped)


def validate_refined_bullet(bullet: str, template_draft: str, allowed_context: str = "") -> str | None:
    clean = " ".join(bullet.replace("\n", " ").split()).strip(" -")
    if not clean or len(clean) > 220:
        return None
    if clean == template_draft:
        return None
    if any(marker in clean.lower() for marker in [" as an ai ", "i don't", "cannot", "unknown"]):
        return None
    allowed_text = normalise_claim_text(f"{template_draft} {allowed_context}")
    for index, token in enumerate(re.findall(r"\b[A-Za-z][A-Za-z0-9.+#/-]*\b", clean)):
        if index == 0 and token[:1].isupper() and token[1:].islower():
            continue
        if is_grounding_sensitive_token(token) and normalise_claim_text(token) not in allowed_text:
            return None
    return clean


def is_grounding_sensitive_token(token: str) -> bool:
    return any(character.isdigit() for character in token) or any(character.isupper() for character in token[1:])


def normalise_claim_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower())
