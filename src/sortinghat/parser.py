from __future__ import annotations

import re
from typing import Iterable, List

from .models import CandidateProfile, ContactInfo, Education, Experience


class ResumeParser:
    """Lightweight heuristics to capture key resume sections from plaintext."""

    EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")

    def __init__(self, text: str):
        self.lines = [line.strip() for line in text.splitlines() if line.strip()]

    def parse(self) -> CandidateProfile:
        profile = CandidateProfile()
        profile.contact = self._extract_contact()
        profile.skills = self._extract_skills()
        profile.summary = self._extract_summary()
        profile.experiences = self._extract_experience()
        profile.education = self._extract_education()
        profile.achievements = self._extract_section("Achievements")
        profile.certifications = self._extract_section("Certifications")
        return profile

    def _extract_contact(self) -> ContactInfo:
        email = self._search_regex(self.EMAIL_RE)
        phone = self._search_regex(self.PHONE_RE)
        name = self.lines[0] if self.lines else ""
        location = self._extract_location()
        return ContactInfo(name=name, email=email, phone=phone, location=location)

    def _extract_location(self) -> str:
        for line in self.lines[:3]:
            if any(city in line.lower() for city in ["remote", "usa", "uk", "canada"]):
                return line
        return ""

    def _search_regex(self, pattern: re.Pattern[str]) -> str:
        for line in self.lines[:5]:
            match = pattern.search(line)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return ""

    def _extract_skills(self) -> List[str]:
        skills = []
        capture = False
        for line in self.lines:
            lower = line.lower()
            if lower.startswith("skills") or lower.startswith("technologies"):
                capture = True
                line = line.split(":", 1)[-1] if ":" in line else ""
            elif capture and not line:
                break
            if capture:
                skills.extend(self._split_list(line))
        return [skill for skill in skills if skill]

    def _extract_summary(self) -> str:
        paragraphs: List[str] = []
        for line in self.lines:
            if line.lower().startswith("summary"):
                continue
            if line.lower().startswith(("experience", "skills", "education")):
                break
            paragraphs.append(line)
            if len(paragraphs) >= 3:
                break
        return " ".join(paragraphs)

    def _extract_experience(self) -> List[Experience]:
        experiences: List[Experience] = []
        capture = False
        buffer: List[str] = []
        for line in self.lines:
            lower = line.lower()
            if lower.startswith("experience"):
                capture = True
                continue
            if capture and lower.startswith("education"):
                break
            if capture:
                if line and any(token in lower for token in ["engineer", "manager", "developer", "intern"]):
                    if buffer:
                        experiences.append(self._experience_from_lines(buffer))
                        buffer = []
                    buffer.append(line)
                else:
                    buffer.append(line)
        if buffer:
            experiences.append(self._experience_from_lines(buffer))
        return experiences

    def _experience_from_lines(self, lines: Iterable[str]) -> Experience:
        lines = list(lines)
        title = lines[0] if lines else ""
        company = lines[1] if len(lines) > 1 else ""
        description = " ".join(lines[2:]) if len(lines) > 2 else ""
        duration = ""
        tools = self._split_list(description)
        return Experience(title=title, company=company, description=description, duration=duration, tools=tools)

    def _extract_education(self) -> List[Education]:
        education: List[Education] = []
        capture = False
        for line in self.lines:
            lower = line.lower()
            if lower.startswith("education"):
                capture = True
                continue
            if capture and lower.startswith(("skills", "experience")):
                break
            if capture:
                institution = line
                degree = ""
                graduation = ""
                education.append(Education(institution=institution, degree=degree, graduation=graduation))
        return education

    def _extract_section(self, name: str) -> List[str]:
        capture = False
        collected: List[str] = []
        for line in self.lines:
            lower = line.lower()
            if lower.startswith(name.lower()):
                capture = True
                continue
            if capture and (":" in line or lower.startswith(("experience", "education", "skills"))):
                break
            if capture:
                collected.extend(self._split_list(line))
        return [entry for entry in collected if entry]

    @staticmethod
    def _split_list(text: str) -> List[str]:
        separators = [",", "|", "/", "•"]
        pattern = "|".join(map(re.escape, separators))
        return [chunk.strip() for chunk in re.split(pattern, text) if chunk.strip()]
