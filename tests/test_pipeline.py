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
