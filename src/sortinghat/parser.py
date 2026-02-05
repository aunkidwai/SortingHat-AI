from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Iterable, List

from .models import CandidateProfile, ContactInfo, Education, Experience

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Section header patterns (case-insensitive)
# ---------------------------------------------------------------------------
SECTION_ALIASES: dict[str, list[str]] = {
    "skills": ["skills", "technologies", "technical skills", "core competencies", "tech stack"],
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "work history",
        "professional background",
        "employment history",
        "employment",
    ],
    "education": ["education", "academic background", "qualifications"],
    "summary": ["summary", "objective", "profile", "about me", "professional summary"],
    "achievements": ["achievements", "accomplishments", "awards", "honors"],
    "certifications": ["certifications", "certificates", "licenses", "credentials"],
}

# Build a flat lookup: lowered alias -> canonical section name
_ALIAS_LOOKUP: dict[str, str] = {}
for _canonical, _aliases in SECTION_ALIASES.items():
    for _alias in _aliases:
        _ALIAS_LOOKUP[_alias] = _canonical

# Role-title keywords used to detect individual experience entries
ROLE_KEYWORDS: list[str] = [
    "engineer",
    "manager",
    "developer",
    "intern",
    "analyst",
    "designer",
    "architect",
    "consultant",
    "director",
    "lead",
    "scientist",
    "administrator",
    "coordinator",
    "specialist",
    "technician",
    "officer",
    "associate",
    "vice president",
    "vp",
    "head of",
    "founder",
    "co-founder",
    "cto",
    "ceo",
    "coo",
    "cfo",
]

# Common non-name first-line patterns
_NON_NAME_PATTERNS: list[str] = [
    "resume",
    "curriculum vitae",
    "cv",
    "cover letter",
    "portfolio",
]


class ResumeParser:
    """Heuristics-based parser that captures key resume sections from plaintext."""

    EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")

    def __init__(self, text: str) -> None:
        self.raw_text = text
        self.lines = [line.strip() for line in text.splitlines() if line.strip()]
        self._section_map: dict[str, tuple[int, int]] = {}
        self._build_section_map()

    # ------------------------------------------------------------------
    # Section detection
    # ------------------------------------------------------------------

    def _classify_line(self, line: str) -> str | None:
        """Return canonical section name if *line* looks like a section header."""
        lower = line.lower().rstrip(":").strip()
        # Direct alias match
        if lower in _ALIAS_LOOKUP:
            return _ALIAS_LOOKUP[lower]
        # Prefix match (e.g. "Skills:" or "Experience  ")
        for alias, canonical in _ALIAS_LOOKUP.items():
            if lower.startswith(alias):
                remainder = lower[len(alias) :]
                if not remainder or remainder[0] in (":", " ", "\t"):
                    return canonical
        return None

    def _build_section_map(self) -> None:
        """Identify start/end line indices for each canonical section."""
        sections: list[tuple[str, int]] = []
        for idx, line in enumerate(self.lines):
            canonical = self._classify_line(line)
            if canonical is not None:
                sections.append((canonical, idx))
        for i, (name, start) in enumerate(sections):
            end = sections[i + 1][1] if i + 1 < len(sections) else len(self.lines)
            self._section_map[name] = (start, end)
        logger.debug("Detected sections: %s", list(self._section_map.keys()))

    def _section_lines(self, name: str) -> list[str]:
        """Return the body lines for a named section (excluding the header)."""
        if name not in self._section_map:
            return []
        start, end = self._section_map[name]
        return self.lines[start + 1 : end]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self) -> CandidateProfile:
        profile = CandidateProfile()
        profile.contact = self._extract_contact()
        profile.skills = self._extract_skills()
        profile.summary = self._extract_summary()
        profile.experiences = self._extract_experience()
        profile.education = self._extract_education()
        profile.achievements = self._extract_section_items("achievements")
        profile.certifications = self._extract_section_items("certifications")
        logger.info(
            "Parsed resume: %s | %d skills | %d experiences",
            profile.contact.name,
            len(profile.skills),
            len(profile.experiences),
        )
        return profile

    # ------------------------------------------------------------------
    # Contact extraction
    # ------------------------------------------------------------------

    def _extract_contact(self) -> ContactInfo:
        email = self._search_regex(self.EMAIL_RE)
        phone = self._search_regex(self.PHONE_RE)
        name = self._extract_name()
        location = self._extract_location()
        return ContactInfo(name=name, email=email, phone=phone, location=location)

    def _extract_name(self) -> str:
        """Return the candidate's name from the first few lines, skipping non-name headers."""
        for line in self.lines[:5]:
            lower = line.lower().strip()
            # Skip lines that look like document titles
            if any(lower.startswith(pat) for pat in _NON_NAME_PATTERNS):
                continue
            # Skip lines that look like section headers
            if self._classify_line(line) is not None:
                continue
            # Skip lines that are purely contact info
            if self.EMAIL_RE.search(line) and not re.search(r"[A-Za-z]{2,}\s+[A-Za-z]{2,}", line):
                continue
            if self.PHONE_RE.search(line) and not re.search(r"[A-Za-z]{2,}\s+[A-Za-z]{2,}", line):
                continue
            return line
        return self.lines[0] if self.lines else ""

    def _extract_location(self) -> str:
        location_keywords = [
            "remote",
            "usa",
            "uk",
            "canada",
            "india",
            "germany",
            "france",
            "australia",
            "singapore",
            "japan",
            "china",
            "brazil",
            "netherlands",
            "sweden",
            "new york",
            "san francisco",
            "london",
            "berlin",
            "toronto",
            "seattle",
            "chicago",
            "boston",
            "los angeles",
            "austin",
            "denver",
            "bangalore",
            "mumbai",
            "hyderabad",
        ]
        for line in self.lines[:5]:
            if any(kw in line.lower() for kw in location_keywords):
                return line
        return ""

    def _search_regex(self, pattern: re.Pattern[str]) -> str:
        for line in self.lines[:5]:
            match = pattern.search(line)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return ""

    # ------------------------------------------------------------------
    # Skills
    # ------------------------------------------------------------------

    def _extract_skills(self) -> List[str]:
        lines = self._section_lines("skills")
        if lines:
            skills: list[str] = []
            for line in lines:
                # Handle inline "Skills: X, Y, Z" on the header line
                skills.extend(self._split_list(line))
            return [s for s in skills if s]

        # Fallback: look for inline "Skills: ..." on the header line itself
        if "skills" in self._section_map:
            header_line = self.lines[self._section_map["skills"][0]]
            after_colon = header_line.split(":", 1)[-1] if ":" in header_line else ""
            if after_colon.strip():
                return [s for s in self._split_list(after_colon) if s]

        # Legacy fallback for unstructured resumes
        return self._extract_skills_legacy()

    def _extract_skills_legacy(self) -> List[str]:
        """Original capture-based fallback for resumes without detectable headers."""
        skills: list[str] = []
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
        return [s for s in skills if s]

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _extract_summary(self) -> str:
        lines = self._section_lines("summary")
        if lines:
            return " ".join(lines[:5])
        # Fallback: grab early lines before any section
        paragraphs: list[str] = []
        first_section_idx = min(
            (start for start, _ in self._section_map.values()),
            default=len(self.lines),
        )
        for line in self.lines[:first_section_idx]:
            if self._classify_line(line) is not None:
                continue
            # Skip contact lines
            if self.EMAIL_RE.search(line) or self.PHONE_RE.search(line):
                continue
            paragraphs.append(line)
            if len(paragraphs) >= 3:
                break
        return " ".join(paragraphs)

    # ------------------------------------------------------------------
    # Experience
    # ------------------------------------------------------------------

    def _extract_experience(self) -> List[Experience]:
        lines = self._section_lines("experience")
        if not lines:
            return []
        experiences: list[Experience] = []
        buffer: list[str] = []
        for line in lines:
            lower = line.lower()
            if self._is_role_title(lower):
                if buffer:
                    experiences.append(self._experience_from_lines(buffer))
                    buffer = []
            buffer.append(line)
        if buffer:
            experiences.append(self._experience_from_lines(buffer))
        return experiences

    @staticmethod
    def _is_role_title(lower_line: str) -> bool:
        return any(kw in lower_line for kw in ROLE_KEYWORDS)

    def _experience_from_lines(self, lines: Iterable[str]) -> Experience:
        lines = list(lines)
        title = lines[0] if lines else ""
        company = lines[1] if len(lines) > 1 else ""
        desc_lines = lines[2:] if len(lines) > 2 else []
        description = " ".join(desc_lines)
        # Extract tool-like tokens (capitalized words, acronyms, known tech)
        tools = self._extract_tools_from_text(description)
        return Experience(title=title, company=company, description=description, duration="", tools=tools)

    @staticmethod
    def _extract_tools_from_text(text: str) -> List[str]:
        """Extract likely tool/technology names from descriptive text."""
        # Match capitalized words, acronyms, and tech-like tokens (e.g. PyTorch, AWS, C++)
        tokens = re.findall(r"\b[A-Z][A-Za-z+#.]*(?:\.[A-Za-z]+)*\b", text)
        # Filter out common English words that happen to start with caps
        stopwords = {
            "Built",
            "Developed",
            "Created",
            "Managed",
            "Led",
            "Designed",
            "Implemented",
            "Deployed",
            "Worked",
            "Collaborated",
            "Improved",
            "Reduced",
            "Increased",
            "The",
            "This",
            "That",
            "Using",
            "With",
            "And",
            "For",
            "From",
            "Into",
        }
        return list(dict.fromkeys(t for t in tokens if t not in stopwords))

    # ------------------------------------------------------------------
    # Education
    # ------------------------------------------------------------------

    def _extract_education(self) -> List[Education]:
        lines = self._section_lines("education")
        if not lines:
            return []
        education: list[Education] = []
        i = 0
        while i < len(lines):
            institution = lines[i]
            degree = ""
            graduation = ""
            # Look ahead for degree / graduation info
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if self._looks_like_degree(next_line):
                    degree = next_line
                    i += 1
                    if i + 1 < len(lines) and self._looks_like_year(lines[i + 1]):
                        graduation = lines[i + 1]
                        i += 1
                elif self._looks_like_year(next_line):
                    graduation = next_line
                    i += 1
            education.append(Education(institution=institution, degree=degree, graduation=graduation))
            i += 1
        return education

    @staticmethod
    def _looks_like_degree(line: str) -> bool:
        degree_keywords = ["bachelor", "master", "phd", "ph.d", "mba", "b.s", "m.s", "b.a", "m.a", "associate", "diploma"]
        lower = line.lower()
        return any(kw in lower for kw in degree_keywords)

    @staticmethod
    def _looks_like_year(line: str) -> bool:
        return bool(re.search(r"\b(19|20)\d{2}\b", line))

    # ------------------------------------------------------------------
    # Generic section extraction
    # ------------------------------------------------------------------

    def _extract_section_items(self, name: str) -> List[str]:
        lines = self._section_lines(name)
        collected: list[str] = []
        for line in lines:
            collected.extend(self._split_list(line))
        return [entry for entry in collected if entry]

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _split_list(text: str) -> List[str]:
        separators = [",", "|", "/", "\u2022", "\u2023", "-"]
        pattern = "|".join(map(re.escape, separators))
        return [chunk.strip() for chunk in re.split(pattern, text) if chunk.strip()]

    # ------------------------------------------------------------------
    # Multi-format loaders
    # ------------------------------------------------------------------

    @classmethod
    def from_file(cls, path: str | Path) -> "ResumeParser":
        """Create a parser from a file path, detecting format automatically."""
        path = Path(path)
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            text = cls._read_pdf(path)
        elif suffix in (".docx", ".doc"):
            text = cls._read_docx(path)
        else:
            text = path.read_text(encoding="utf-8")
        return cls(text)

    @staticmethod
    def _read_pdf(path: Path) -> str:
        try:
            import pdfplumber
        except ImportError:
            raise ImportError(
                "pdfplumber is required to parse PDF files. "
                "Install it with: pip install sortinghat-ai[pdf]"
            )
        pages: list[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        return "\n".join(pages)

    @staticmethod
    def _read_docx(path: Path) -> str:
        try:
            import docx
        except ImportError:
            raise ImportError(
                "python-docx is required to parse DOCX files. "
                "Install it with: pip install sortinghat-ai[docx]"
            )
        document = docx.Document(str(path))
        return "\n".join(para.text for para in document.paragraphs if para.text.strip())
