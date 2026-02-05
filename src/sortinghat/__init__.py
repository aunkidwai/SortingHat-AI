"""SortingHat AI — resume parsing, scoring, and LLM-enhanced matching."""

from .llm import LLMResponse, OllamaClient
from .models import CandidateProfile, ContactInfo, Education, Experience
from .parser import ResumeParser
from .pipeline import PipelineResult, ResumePipeline
from .scoring import JobMatchScorer, MatchBreakdown, canonicalize_skill

__all__ = [
    "CandidateProfile",
    "ContactInfo",
    "Education",
    "Experience",
    "JobMatchScorer",
    "LLMResponse",
    "MatchBreakdown",
    "OllamaClient",
    "PipelineResult",
    "ResumeParser",
    "ResumePipeline",
    "canonicalize_skill",
]
