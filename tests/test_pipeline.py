from unittest.mock import MagicMock, patch

from sortinghat.pipeline import ResumePipeline


RESUME_TEXT = """
Jane Doe
jane.doe@example.com | +1 555 123 4567
Remote, USA
Summary
Machine learning engineer with experience building NLP systems and deploying models to production.
Skills: Python, PyTorch, NLP, Docker, AWS
Experience
Machine Learning Engineer
Acme Corp
Built NLP classifiers using PyTorch and deployed them via Docker on AWS.
Education
State University
"""


JOB_DESCRIPTION = """
We are seeking an ML engineer proficient in Python, PyTorch, Docker, and AWS services. NLP experience is required.
"""


def test_pipeline_scores_resume():
    pipeline = ResumePipeline(JOB_DESCRIPTION, required_skills=["Python", "PyTorch", "NLP"], optional_skills=["Docker", "AWS"])
    result = pipeline.run(RESUME_TEXT)

    assert result.breakdown.required_coverage == 100.0
    assert result.breakdown.optional_coverage == 100.0
    assert result.breakdown.overall_score >= 90
    assert any("evidence" in rec.lower() or "tailor" in rec.lower() for rec in result.recommendations) is False


def test_recommendations_for_missing_skills():
    pipeline = ResumePipeline(JOB_DESCRIPTION, required_skills=["Python", "PyTorch", "Kubernetes"], optional_skills=["Docker"])
    result = pipeline.run(RESUME_TEXT)

    assert any("Kubernetes" in rec for rec in result.recommendations)
    assert result.breakdown.required_coverage < 100


def test_pipeline_result_has_profile():
    pipeline = ResumePipeline(JOB_DESCRIPTION, required_skills=["Python"])
    result = pipeline.run(RESUME_TEXT)
    assert result.profile.contact.name == "Jane Doe"
    assert result.profile.contact.email == "jane.doe@example.com"


def test_pipeline_heuristic_experience_recommendation():
    # Resume with skills but no experience mentioning them
    sparse_resume = """
Bob Test
bob@test.com
Skills: Rust, Go, Terraform
Experience
Manager
SomeCo
Managed a team of 10 people.
Education
University
"""
    pipeline = ResumePipeline("", required_skills=["Rust", "Go", "Terraform"])
    result = pipeline.run(sparse_resume)
    assert any("impact" in r.lower() or "bullets" in r.lower() for r in result.recommendations)


def test_pipeline_optional_missing_recommendation():
    pipeline = ResumePipeline(JOB_DESCRIPTION, required_skills=["Python"], optional_skills=["Kubernetes", "Terraform"])
    result = pipeline.run(RESUME_TEXT)
    assert any("optional" in r.lower() for r in result.recommendations)


def test_pipeline_well_aligned_recommendation():
    pipeline = ResumePipeline(JOB_DESCRIPTION, required_skills=["Python", "PyTorch", "NLP"], optional_skills=["Docker", "AWS"])
    result = pipeline.run(RESUME_TEXT)
    assert any("well-aligned" in r.lower() or "highlight" in r.lower() for r in result.recommendations)


def test_pipeline_empty_resume():
    pipeline = ResumePipeline(JOB_DESCRIPTION, required_skills=["Python"])
    result = pipeline.run("")
    assert result.breakdown.required_coverage == 0.0
    assert len(result.recommendations) > 0


def test_pipeline_without_llm():
    pipeline = ResumePipeline(JOB_DESCRIPTION, required_skills=["Python"], use_llm=False)
    assert pipeline.llm is None
    result = pipeline.run(RESUME_TEXT)
    assert result.breakdown.required_coverage == 100.0


def test_pipeline_llm_fallback_when_unavailable():
    """When use_llm=True but Ollama is not running, pipeline should fall back gracefully."""
    pipeline = ResumePipeline(
        JOB_DESCRIPTION,
        required_skills=["Python"],
        use_llm=True,
        llm_base_url="http://localhost:99999",  # unreachable
    )
    # LLM should be None because is_available() returned False
    assert pipeline.llm is None
    result = pipeline.run(RESUME_TEXT)
    assert result.breakdown.required_coverage == 100.0
