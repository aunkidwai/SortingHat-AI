from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from .models import CandidateProfile
from .parser import ResumeParser
from .scoring import JobMatchScorer, MatchBreakdown


@dataclass
class PipelineResult:
    profile: CandidateProfile
    breakdown: MatchBreakdown
    recommendations: List[str]


class ResumePipeline:
    """Orchestrates parsing, normalization, and scoring in a single pass."""

    def __init__(self, job_description: str, required_skills: Sequence[str] | None = None, optional_skills: Sequence[str] | None = None):
        self.job_description = job_description
        self.scorer = JobMatchScorer(job_description, required_skills=required_skills, optional_skills=optional_skills)

    def run(self, resume_text: str) -> PipelineResult:
        parser = ResumeParser(resume_text)
        profile = parser.parse()
        breakdown = self.scorer.score(profile)
        recommendations = self._generate_recommendations(profile, breakdown)
        return PipelineResult(profile=profile, breakdown=breakdown, recommendations=recommendations)

    def _generate_recommendations(self, profile: CandidateProfile, breakdown: MatchBreakdown) -> List[str]:
        recs: List[str] = []
        missing_required = self.scorer.required_skills.difference(profile.normalized_skills())
        if missing_required:
            formatted_missing = ", ".join(skill.title() for skill in sorted(missing_required))
            recs.append(f"Add evidence for required skills: {formatted_missing}.")
        if breakdown.experience_alignment < 70:
            recs.append("Provide impact-focused bullets that mention the requested tools in your recent experience.")
        if not recs:
            recs.append("Profile is well-aligned. Highlight recent wins in the summary.")
        return recs
