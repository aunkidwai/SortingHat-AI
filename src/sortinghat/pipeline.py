from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Sequence

from .llm import OllamaClient
from .models import CandidateProfile
from .parser import ResumeParser
from .scoring import JobMatchScorer, MatchBreakdown, canonicalize_skill

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    profile: CandidateProfile
    breakdown: MatchBreakdown
    recommendations: List[str]


class ResumePipeline:
    """Orchestrates parsing, normalization, scoring, and recommendation in a single pass."""

    def __init__(
        self,
        job_description: str,
        required_skills: Sequence[str] | None = None,
        optional_skills: Sequence[str] | None = None,
        use_llm: bool = False,
        llm_model: str = "codellama:34b",
        llm_base_url: str = "http://localhost:11434",
    ) -> None:
        self.job_description = job_description
        self.use_llm = use_llm
        self.llm: OllamaClient | None = None

        # Optionally use LLM to extract skills from JD
        if use_llm:
            self.llm = OllamaClient(model=llm_model, base_url=llm_base_url)
            if self.llm.is_available():
                logger.info("Ollama connected (%s at %s)", llm_model, llm_base_url)
                if required_skills is None and optional_skills is None:
                    extracted = self.llm.extract_skills_from_jd(job_description)
                    required_skills = extracted.get("required") or None
                    optional_skills = extracted.get("optional") or None
                    logger.info(
                        "LLM extracted %d required / %d optional skills",
                        len(required_skills or []),
                        len(optional_skills or []),
                    )
            else:
                logger.warning("Ollama not available — falling back to heuristic mode")
                self.llm = None

        self.scorer = JobMatchScorer(
            job_description,
            required_skills=required_skills,
            optional_skills=optional_skills,
        )

    def run(self, resume_text: str) -> PipelineResult:
        parser = ResumeParser(resume_text)
        profile = parser.parse()
        breakdown = self.scorer.score(profile)
        recommendations = self._generate_recommendations(profile, breakdown)
        logger.info("Pipeline complete — overall score: %.1f", breakdown.overall_score)
        return PipelineResult(profile=profile, breakdown=breakdown, recommendations=recommendations)

    def _generate_recommendations(self, profile: CandidateProfile, breakdown: MatchBreakdown) -> List[str]:
        # Try LLM-powered recommendations first
        if self.llm is not None:
            try:
                missing = sorted(self.scorer.missing_required(profile))
                llm_text = self.llm.enhance_recommendations(
                    resume_summary=profile.summary,
                    skills=[s for s in profile.normalized_skills()],
                    missing_skills=missing,
                    job_description=self.job_description,
                    score=breakdown.overall_score,
                )
                if llm_text.strip():
                    recs = [line.strip().lstrip("•-*123456789. ") for line in llm_text.strip().splitlines() if line.strip()]
                    if recs:
                        logger.info("Using LLM-generated recommendations")
                        return recs
            except (ConnectionError, OSError):
                logger.warning("LLM recommendation failed — using heuristic fallback")

        return self._heuristic_recommendations(profile, breakdown)

    def _heuristic_recommendations(self, profile: CandidateProfile, breakdown: MatchBreakdown) -> List[str]:
        recs: List[str] = []
        missing_required = self.scorer.missing_required(profile)
        if missing_required:
            formatted = ", ".join(skill.title() for skill in sorted(missing_required))
            recs.append(f"Add evidence for required skills: {formatted}.")

        missing_optional = self.scorer.missing_optional(profile)
        if missing_optional:
            formatted = ", ".join(skill.title() for skill in sorted(missing_optional))
            recs.append(f"Consider adding optional skills: {formatted}.")

        if breakdown.experience_alignment < 70:
            recs.append("Provide impact-focused bullets that mention the requested tools in your recent experience.")
        if not recs:
            recs.append("Profile is well-aligned. Highlight recent wins in the summary.")
        return recs
