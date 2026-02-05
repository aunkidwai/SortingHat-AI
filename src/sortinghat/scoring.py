from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from .models import CandidateProfile

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Skill synonym map  (canonical -> set of aliases, all lowercase)
# ---------------------------------------------------------------------------
SKILL_SYNONYMS: dict[str, set[str]] = {
    "javascript": {"js", "ecmascript", "es6", "es2015"},
    "typescript": {"ts"},
    "python": {"py", "python3", "cpython"},
    "kubernetes": {"k8s", "kube"},
    "machine learning": {"ml"},
    "deep learning": {"dl"},
    "natural language processing": {"nlp"},
    "artificial intelligence": {"ai"},
    "amazon web services": {"aws"},
    "google cloud platform": {"gcp", "google cloud"},
    "microsoft azure": {"azure"},
    "react": {"reactjs", "react.js"},
    "angular": {"angularjs", "angular.js"},
    "vue": {"vuejs", "vue.js"},
    "node": {"nodejs", "node.js"},
    "postgres": {"postgresql", "psql"},
    "mysql": {"mariadb"},
    "mongodb": {"mongo"},
    "docker": {"containerization"},
    "ci/cd": {"cicd", "continuous integration", "continuous deployment"},
    "tensorflow": {"tf"},
    "pytorch": {"torch"},
    "c++": {"cpp"},
    "c#": {"csharp", "c sharp"},
    "objective-c": {"objc"},
    "ruby on rails": {"rails", "ror"},
    "rest": {"restful", "rest api", "restful api"},
    "graphql": {"gql"},
    "html": {"html5"},
    "css": {"css3"},
    "sass": {"scss"},
}

# Build reverse lookup: alias -> canonical
_SYNONYM_REVERSE: dict[str, str] = {}
for _canon, _aliases in SKILL_SYNONYMS.items():
    _SYNONYM_REVERSE[_canon] = _canon
    for _alias in _aliases:
        _SYNONYM_REVERSE[_alias] = _canon

# Common English words to exclude from auto-extracted skills
_JD_STOPWORDS: set[str] = {
    "the", "and", "for", "with", "our", "you", "your", "are", "will",
    "have", "has", "this", "that", "from", "into", "not", "but", "also",
    "who", "can", "all", "been", "were", "being", "their", "its", "more",
    "about", "than", "them", "these", "those", "then", "when", "how",
    "what", "which", "where", "would", "should", "could", "may", "might",
    "must", "shall", "need", "want", "like", "just", "use", "using",
    "used", "work", "team", "role", "experience", "years", "ability",
    "strong", "knowledge", "understanding", "working", "looking",
    "seeking", "required", "preferred", "plus", "nice", "including",
    "etc", "such", "well", "good", "great", "excellent", "proficient",
}


def canonicalize_skill(skill: str) -> str:
    """Resolve a skill string to its canonical form via synonym lookup."""
    lower = skill.lower().strip()
    return _SYNONYM_REVERSE.get(lower, lower)


@dataclass
class MatchBreakdown:
    required_coverage: float
    optional_coverage: float
    experience_alignment: float

    @property
    def overall_score(self) -> float:
        return round(
            (self.required_coverage * 0.6)
            + (self.optional_coverage * 0.2)
            + (self.experience_alignment * 0.2),
            2,
        )


class JobMatchScorer:
    """Scores a profile against a job description using heuristics + synonym matching."""

    def __init__(
        self,
        job_description: str,
        required_skills: Sequence[str] | None = None,
        optional_skills: Sequence[str] | None = None,
    ) -> None:
        self.job_description = job_description
        self.required_skills = (
            self._normalize(required_skills) if required_skills else self._extract_skills(job_description)
        )
        self.optional_skills = self._normalize(optional_skills)

    def score(self, profile: CandidateProfile) -> MatchBreakdown:
        candidate_skills = {canonicalize_skill(s) for s in profile.normalized_skills()}
        required_canonical = {canonicalize_skill(s) for s in self.required_skills}
        optional_canonical = {canonicalize_skill(s) for s in self.optional_skills}

        required_hits = candidate_skills.intersection(required_canonical)
        optional_hits = candidate_skills.intersection(optional_canonical)

        required_coverage = len(required_hits) / len(required_canonical) if required_canonical else 0.0
        optional_coverage = len(optional_hits) / len(optional_canonical) if optional_canonical else 0.0
        experience_alignment = self._score_experience(profile, required_canonical)

        breakdown = MatchBreakdown(
            required_coverage=round(required_coverage * 100, 2),
            optional_coverage=round(optional_coverage * 100, 2),
            experience_alignment=round(experience_alignment * 100, 2),
        )
        logger.debug(
            "Score breakdown: req=%.1f%% opt=%.1f%% exp=%.1f%% overall=%.1f",
            breakdown.required_coverage,
            breakdown.optional_coverage,
            breakdown.experience_alignment,
            breakdown.overall_score,
        )
        return breakdown

    def _score_experience(self, profile: CandidateProfile, target_skills: set[str]) -> float:
        """Graduated experience alignment: measures how many target skills appear across experiences."""
        if not profile.experiences or not target_skills:
            return 0.0
        found_skills: set[str] = set()
        for exp in profile.experiences:
            combined_text = " ".join([exp.title, exp.company, exp.description]).lower()
            for skill in target_skills:
                # Check canonical form and known aliases
                forms = {skill}
                if skill in SKILL_SYNONYMS:
                    forms.update(SKILL_SYNONYMS[skill])
                # Also check the raw form
                raw_forms = {s for s in self.required_skills if canonicalize_skill(s) == skill}
                forms.update(raw_forms)
                if any(form in combined_text for form in forms):
                    found_skills.add(skill)
        return len(found_skills) / len(target_skills)

    def _extract_skills(self, text: str) -> set[str]:
        """Extract likely skill tokens from a job description, filtering stopwords."""
        tokens = re.findall(r"[A-Za-z+#./]+", text)
        skills: set[str] = set()
        for token in tokens:
            lower = token.lower().strip(".")
            if len(lower) <= 1:
                continue
            if lower in _JD_STOPWORDS:
                continue
            skills.add(lower)
        logger.debug("Auto-extracted %d skills from job description", len(skills))
        return skills

    @staticmethod
    def _normalize(items: Sequence[str] | None) -> set[str]:
        if not items:
            return set()
        return {item.lower().strip() for item in items if item.strip()}

    def missing_required(self, profile: CandidateProfile) -> set[str]:
        """Return required skills (canonical) not found in the candidate profile."""
        candidate_skills = {canonicalize_skill(s) for s in profile.normalized_skills()}
        required_canonical = {canonicalize_skill(s) for s in self.required_skills}
        return required_canonical - candidate_skills

    def missing_optional(self, profile: CandidateProfile) -> set[str]:
        """Return optional skills (canonical) not found in the candidate profile."""
        candidate_skills = {canonicalize_skill(s) for s in profile.normalized_skills()}
        optional_canonical = {canonicalize_skill(s) for s in self.optional_skills}
        return optional_canonical - candidate_skills
