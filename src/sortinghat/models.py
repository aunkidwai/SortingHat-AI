from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


def _clean(value: str | None) -> str:
    return value.strip() if value else ""


@dataclass
class ContactInfo:
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""

    def merge(self, other: "ContactInfo") -> "ContactInfo":
        return ContactInfo(
            name=_clean(self.name) or _clean(other.name),
            email=_clean(self.email) or _clean(other.email),
            phone=_clean(self.phone) or _clean(other.phone),
            location=_clean(self.location) or _clean(other.location),
        )


@dataclass
class Experience:
    title: str
    company: str
    description: str = ""
    duration: str = ""
    tools: List[str] = field(default_factory=list)


@dataclass
class Education:
    institution: str
    degree: str = ""
    graduation: str = ""


@dataclass
class CandidateProfile:
    contact: ContactInfo = field(default_factory=ContactInfo)
    summary: str = ""
    skills: List[str] = field(default_factory=list)
    experiences: List[Experience] = field(default_factory=list)
    education: List[Education] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)

    def normalized_skills(self) -> List[str]:
        return sorted({skill.lower().strip() for skill in self.skills if skill.strip()})

    def short_experience_highlights(self) -> List[str]:
        highlights: List[str] = []
        for exp in self.experiences:
            prefix = f"{exp.title} at {exp.company}".strip()
            if exp.description:
                highlights.append(f"{prefix}: {exp.description}")
            else:
                highlights.append(prefix)
        return highlights
