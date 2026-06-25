import json
import re
from dataclasses import dataclass
from functools import lru_cache

from app.services.paths import DATA_DIR

DEFAULT_TAXONOMY = {
    "languages": ["Python", "TypeScript", "JavaScript", "C", "C++", "Java", "SQL"],
    "web": ["React", "Next.js", "Node.js", "REST APIs", "GraphQL", "HTML/CSS"],
    "data_ai": ["Pandas", "NumPy", "Machine Learning", "LLMs", "RAG", "Data Pipelines", "Data Visualisation"],
    "cloud_devops": ["Git", "GitHub", "Docker", "CI/CD", "AWS", "Azure", "GCP", "Linux", "Testing"],
    "databases": ["SQLite", "PostgreSQL", "MySQL", "MongoDB", "Redis"],
    "embedded": ["Embedded C", "STM32", "Microcontrollers", "CAN", "UART", "SPI", "I2C", "RTOS", "PCB Design"],
    "professional": ["Technical Communication", "Project Ownership", "Agile", "Stakeholder Communication", "Team Leadership"],
}

DEFAULT_ALIASES = {
    "Postgres": "PostgreSQL",
    "React.js": "React",
    "RESTful APIs": "REST APIs",
    "Github": "GitHub",
    "Docker Compose": "Docker",
    "C/C++": "C++",
    "Typescript": "TypeScript",
    "Javascript": "JavaScript",
    "Node": "Node.js",
    "NodeJS": "Node.js",
    "Node.js backend": "Node.js",
    "CI CD": "CI/CD",
    "CI-CD": "CI/CD",
    "Gemini": "LLMs",
    "OpenAI": "LLMs",
    "LLM": "LLMs",
    "AI/ML": "Machine Learning",
    "ML": "Machine Learning",
    "PostgreSQL storage": "PostgreSQL",
    "STM32U5": "STM32",
    "FreeRTOS": "RTOS",
    "CAN-bus": "CAN",
    "WebSockets": "REST APIs",
}

@dataclass(frozen=True)
class SkillTaxonomy:
    taxonomy: dict[str, list[str]]
    aliases: dict[str, str]

    @property
    def all_skills(self) -> list[str]:
        return sorted({skill for skills in self.taxonomy.values() for skill in skills})


def _clean_key(value: str) -> str:
    return " ".join(value.strip().split())


def _load_from_data_file() -> tuple[dict[str, list[str]], dict[str, str]]:
    path = DATA_DIR / "skill_taxonomy.json"
    if not path.exists():
        return DEFAULT_TAXONOMY, DEFAULT_ALIASES

    payload = json.loads(path.read_text(encoding="utf-8"))
    taxonomy = payload.get("taxonomy", DEFAULT_TAXONOMY)
    aliases = {**DEFAULT_ALIASES, **payload.get("aliases", {})}
    return taxonomy, aliases


@lru_cache(maxsize=1)
def load_skill_taxonomy() -> SkillTaxonomy:
    taxonomy, aliases = _load_from_data_file()
    canonical_lookup = {
        _clean_key(skill).casefold(): skill
        for skills in taxonomy.values()
        for skill in skills
    }

    normalized_aliases: dict[str, str] = {}
    for alias, canonical in aliases.items():
        clean_alias = _clean_key(alias)
        clean_canonical = _clean_key(canonical)
        normalized_aliases[clean_alias] = canonical_lookup.get(clean_canonical.casefold(), clean_canonical)

    return SkillTaxonomy(taxonomy=taxonomy, aliases=normalized_aliases)


def canonicalize_skill_name(name: str) -> str:
    taxonomy = load_skill_taxonomy()
    clean = _clean_key(name)
    for skill in taxonomy.all_skills:
        if clean.casefold() == skill.casefold():
            return skill
    for alias, canonical in taxonomy.aliases.items():
        if clean.casefold() == alias.casefold():
            return canonical
    return clean


def variants_for(skill: str) -> list[str]:
    taxonomy = load_skill_taxonomy()
    canonical = canonicalize_skill_name(skill)
    aliases = [alias for alias, target in taxonomy.aliases.items() if target == canonical]
    return [canonical, *aliases]


def skill_pattern(variant: str) -> re.Pattern[str]:
    escaped = re.escape(variant).replace(r"\ ", r"[\s-]+")
    return re.compile(rf"(?<![A-Za-z0-9+#]){escaped}(?![A-Za-z0-9+#])", re.IGNORECASE)
