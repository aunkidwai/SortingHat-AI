import pytest

from sortinghat.models import CandidateProfile, Experience
from sortinghat.scoring import JobMatchScorer, MatchBreakdown, canonicalize_skill


class TestCanonicalizeSkill:
    def test_known_synonym(self):
        assert canonicalize_skill("JS") == "javascript"
        assert canonicalize_skill("js") == "javascript"

    def test_canonical_stays(self):
        assert canonicalize_skill("python") == "python"
        assert canonicalize_skill("Python") == "python"

    def test_unknown_passthrough(self):
        assert canonicalize_skill("foobar") == "foobar"

    def test_kubernetes_aliases(self):
        assert canonicalize_skill("k8s") == "kubernetes"
        assert canonicalize_skill("kube") == "kubernetes"

    def test_nlp_alias(self):
        assert canonicalize_skill("NLP") == "natural language processing"

    def test_react_aliases(self):
        assert canonicalize_skill("ReactJS") == "react"
        assert canonicalize_skill("react.js") == "react"


class TestMatchBreakdown:
    def test_overall_score_formula(self):
        b = MatchBreakdown(required_coverage=100, optional_coverage=100, experience_alignment=100)
        assert b.overall_score == 100.0

    def test_weighted_calculation(self):
        b = MatchBreakdown(required_coverage=50, optional_coverage=50, experience_alignment=50)
        assert b.overall_score == 50.0

    def test_zero_scores(self):
        b = MatchBreakdown(required_coverage=0, optional_coverage=0, experience_alignment=0)
        assert b.overall_score == 0.0


class TestJobMatchScorer:
    def test_perfect_match(self):
        profile = CandidateProfile(skills=["Python", "Docker", "AWS"])
        scorer = JobMatchScorer("", required_skills=["Python", "Docker"], optional_skills=["AWS"])
        breakdown = scorer.score(profile)
        assert breakdown.required_coverage == 100.0
        assert breakdown.optional_coverage == 100.0

    def test_partial_match(self):
        profile = CandidateProfile(skills=["Python"])
        scorer = JobMatchScorer("", required_skills=["Python", "Docker"])
        breakdown = scorer.score(profile)
        assert breakdown.required_coverage == 50.0

    def test_no_match(self):
        profile = CandidateProfile(skills=["Ruby"])
        scorer = JobMatchScorer("", required_skills=["Python", "Docker"])
        breakdown = scorer.score(profile)
        assert breakdown.required_coverage == 0.0

    def test_synonym_matching(self):
        profile = CandidateProfile(skills=["JS", "k8s"])
        scorer = JobMatchScorer("", required_skills=["JavaScript", "Kubernetes"])
        breakdown = scorer.score(profile)
        assert breakdown.required_coverage == 100.0

    def test_empty_required(self):
        profile = CandidateProfile(skills=["Python"])
        scorer = JobMatchScorer("", required_skills=[], optional_skills=["Python"])
        breakdown = scorer.score(profile)
        assert breakdown.required_coverage == 0.0
        assert breakdown.optional_coverage == 100.0

    def test_empty_profile_skills(self):
        profile = CandidateProfile(skills=[])
        scorer = JobMatchScorer("", required_skills=["Python"])
        breakdown = scorer.score(profile)
        assert breakdown.required_coverage == 0.0

    def test_experience_alignment_graduated(self):
        profile = CandidateProfile(
            skills=["Python", "Docker", "AWS"],
            experiences=[
                Experience(title="Dev", company="Co", description="Used Python and Docker daily"),
            ],
        )
        scorer = JobMatchScorer("", required_skills=["Python", "Docker", "AWS"])
        breakdown = scorer.score(profile)
        # Python and Docker appear in experience, AWS does not → 2/3
        assert breakdown.experience_alignment == pytest.approx(66.67, abs=0.1)

    def test_experience_alignment_no_experiences(self):
        profile = CandidateProfile(skills=["Python"])
        scorer = JobMatchScorer("", required_skills=["Python"])
        breakdown = scorer.score(profile)
        assert breakdown.experience_alignment == 0.0

    def test_extract_skills_filters_stopwords(self):
        scorer = JobMatchScorer(
            "We are looking for a Python developer with strong Docker skills and AWS experience",
            required_skills=None,
        )
        # Common words like "are", "for", "with", "and" should be filtered
        assert "are" not in scorer.required_skills
        assert "for" not in scorer.required_skills
        assert "with" not in scorer.required_skills
        # Tech terms should remain
        assert "python" in scorer.required_skills
        assert "docker" in scorer.required_skills


class TestMissingSkills:
    def test_missing_required(self):
        profile = CandidateProfile(skills=["Python"])
        scorer = JobMatchScorer("", required_skills=["Python", "Docker"])
        missing = scorer.missing_required(profile)
        assert "docker" in missing
        assert "python" not in missing

    def test_missing_optional(self):
        profile = CandidateProfile(skills=["Python"])
        scorer = JobMatchScorer("", required_skills=["Python"], optional_skills=["Docker", "Terraform"])
        missing = scorer.missing_optional(profile)
        assert "docker" in missing
        assert "terraform" in missing

    def test_synonym_not_missing(self):
        profile = CandidateProfile(skills=["JS"])
        scorer = JobMatchScorer("", required_skills=["JavaScript"])
        missing = scorer.missing_required(profile)
        assert len(missing) == 0
