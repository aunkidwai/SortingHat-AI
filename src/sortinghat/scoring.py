from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from .models import CandidateProfile


@dataclass
class MatchBreakdown:
    required_coverage: float
    optional_coverage: float
    experience_alignment: float

    @property
    def overall_score(self) -> float:
        return round((self.required_coverage * 0.6) + (self.optional_coverage * 0.2) + (self.experience_alignment * 0.2), 2)


class JobMatchScorer:
    """Scores a profile against a job description using lightweight heuristics."""

    def __init__(self, job_description: str, required_skills: Sequence[str] | None = None, optional_skills: Sequence[str] | None = None):
        self.job_description = job_description
        self.required_skills = self._normalize(required_skills) if required_skills else self._extract_skills(job_description)
        self.optional_skills = self._normalize(optional_skills)

    def score(self, profile: CandidateProfile) -> MatchBreakdown:
        candidate_skills = set(profile.normalized_skills())
        required_hits = candidate_skills.intersection(self.required_skills)
        optional_hits = candidate_skills.intersection(self.optional_skills)

        required_coverage = len(required_hits) / len(self.required_skills) if self.required_skills else 0.0
        optional_coverage = len(optional_hits) / len(self.optional_skills) if self.optional_skills else 0.0
        experience_alignment = self._score_experience(profile, self.required_skills)

        return MatchBreakdown(
            required_coverage=round(required_coverage * 100, 2),
            optional_coverage=round(optional_coverage * 100, 2),
            experience_alignment=round(experience_alignment * 100, 2),
        )

    def _score_experience(self, profile: CandidateProfile, target_skills: Iterable[str]) -> float:
        if not profile.experiences:
            return 0.0
        signals = 0
        total = 0
        for exp in profile.experiences:
            total += 1
            combined_text = " ".join([exp.title, exp.company, exp.description]).lower()
            if any(skill in combined_text for skill in target_skills):
                signals += 1
        return signals / total if total else 0.0

    def _extract_skills(self, text: str) -> set[str]:
        tokens = re.findall(r"[A-Za-z+#\.]+", text)
        return {token.lower() for token in tokens if len(token) > 2}

    @staticmethod
    def _normalize(items: Sequence[str]) -> set[str]:
        return {item.lower().strip() for item in items if item.strip()}
