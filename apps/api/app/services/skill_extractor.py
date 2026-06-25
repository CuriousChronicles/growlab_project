import re
from dataclasses import dataclass


SKILL_TAXONOMY = {
    "languages": ["Python", "TypeScript", "JavaScript", "C", "C++", "Java", "SQL"],
    "web": ["React", "Next.js", "Node.js", "REST APIs", "GraphQL", "HTML/CSS"],
    "data_ai": ["Pandas", "NumPy", "Machine Learning", "LLMs", "RAG", "Data Pipelines", "Data Visualisation"],
    "cloud_devops": ["Git", "GitHub", "Docker", "CI/CD", "AWS", "Azure", "GCP", "Linux", "Testing"],
    "databases": ["SQLite", "PostgreSQL", "MySQL", "MongoDB", "Redis"],
    "embedded": ["Embedded C", "STM32", "Microcontrollers", "CAN", "UART", "SPI", "I2C", "RTOS", "PCB Design"],
    "professional": ["Technical Communication", "Project Ownership", "Agile", "Stakeholder Communication", "Team Leadership"],
}

ALIASES = {
    "Postgres": "PostgreSQL",
    "React.js": "React",
    "RESTful APIs": "REST APIs",
    "Github": "GitHub",
    "Docker Compose": "Docker",
    "C/C++": "C++",
    "Typescript": "TypeScript",
    "Javascript": "JavaScript",
    "Node": "Node.js",
    "CI CD": "CI/CD",
    "STM32U5": "STM32",
    "FreeRTOS": "RTOS",
    "Gemini": "LLMs",
}

ALL_SKILLS = sorted({skill for skills in SKILL_TAXONOMY.values() for skill in skills})


def _variants(skill: str) -> list[str]:
    aliases = [alias for alias, canonical in ALIASES.items() if canonical == skill]
    return [skill, *aliases]


def mentions_skill(text: str, skill: str) -> bool:
    haystack = text or ""
    for variant in _variants(skill):
        escaped = re.escape(variant).replace("\\ ", r"[\s-]+")
        if re.search(rf"(?<![A-Za-z0-9+#]){escaped}(?![A-Za-z0-9+#])", haystack, re.IGNORECASE):
            return True
    return False


def extract_skills(text: str) -> set[str]:
    return {skill for skill in ALL_SKILLS if mentions_skill(text, skill)}


@dataclass(frozen=True)
class EvidenceHit:
    source: str
    excerpt: str
    confidence: str


def find_resume_evidence(resume_text: str, skill: str) -> list[EvidenceHit]:
    if not resume_text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+|\n+", resume_text)
    hits: list[EvidenceHit] = []
    action_words = re.compile(r"\b(built|created|implemented|designed|delivered|completed|led|integrated|deployed|tested|automated|analysed|developed)\b", re.I)
    for sentence in sentences:
        clean = " ".join(sentence.split())
        if clean and mentions_skill(clean, skill):
            confidence = "high" if action_words.search(clean) else "low"
            hits.append(EvidenceHit(source="resume", excerpt=clean[:220], confidence=confidence))
    return hits[:3]
