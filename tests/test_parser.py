import pytest

from sortinghat.parser import ResumeParser


FULL_RESUME = """
Jane Doe
jane.doe@example.com | +1 555 123 4567
Remote, USA

Summary
Machine learning engineer with 5 years of experience building NLP systems.

Skills: Python, PyTorch, NLP, Docker, AWS

Experience
Machine Learning Engineer
Acme Corp
Built NLP classifiers using PyTorch and deployed them via Docker on AWS.

Data Analyst
OldCo
Analyzed sales data and created dashboards.

Education
State University
Bachelor of Science in Computer Science
2018

Certifications
AWS Solutions Architect, Google Cloud Professional

Achievements
Best Paper Award, Dean's List
"""

MINIMAL_RESUME = """John Smith
john@test.com
"""

CV_HEADER_RESUME = """Curriculum Vitae
Alice Johnson
alice@example.com
London, UK

Skills
React, TypeScript, Node.js

Work Experience
Frontend Developer
TechCo
Built web applications using React and TypeScript.
"""


class TestContactExtraction:
    def test_email(self):
        p = ResumeParser(FULL_RESUME).parse()
        assert p.contact.email == "jane.doe@example.com"

    def test_phone(self):
        p = ResumeParser(FULL_RESUME).parse()
        assert "555 123 4567" in p.contact.phone

    def test_name_skips_cv_header(self):
        p = ResumeParser(CV_HEADER_RESUME).parse()
        assert p.contact.name == "Alice Johnson"

    def test_name_first_line(self):
        p = ResumeParser(FULL_RESUME).parse()
        assert p.contact.name == "Jane Doe"

    def test_location_usa(self):
        p = ResumeParser(FULL_RESUME).parse()
        assert "USA" in p.contact.location

    def test_location_uk(self):
        p = ResumeParser(CV_HEADER_RESUME).parse()
        assert "UK" in p.contact.location


class TestSkillsExtraction:
    def test_inline_skills(self):
        p = ResumeParser(FULL_RESUME).parse()
        skills = p.normalized_skills()
        assert "python" in skills
        assert "pytorch" in skills
        assert "docker" in skills

    def test_multiline_skills(self):
        text = """Bob Test
Skills
Python
Java
Docker
Experience
Dev at Co
"""
        p = ResumeParser(text).parse()
        skills = p.normalized_skills()
        assert "python" in skills
        assert "java" in skills

    def test_no_skills_section(self):
        p = ResumeParser(MINIMAL_RESUME).parse()
        assert p.skills == []

    def test_alternate_header(self):
        text = """Test User
Technical Skills: Rust, Go, Python
Experience
Developer
SomeCo
"""
        p = ResumeParser(text).parse()
        skills = p.normalized_skills()
        assert "rust" in skills
        assert "go" in skills


class TestExperienceExtraction:
    def test_multiple_experiences(self):
        p = ResumeParser(FULL_RESUME).parse()
        assert len(p.experiences) == 2

    def test_experience_titles(self):
        p = ResumeParser(FULL_RESUME).parse()
        titles = [e.title for e in p.experiences]
        assert "Machine Learning Engineer" in titles
        assert "Data Analyst" in titles

    def test_experience_company(self):
        p = ResumeParser(FULL_RESUME).parse()
        assert p.experiences[0].company == "Acme Corp"

    def test_experience_description(self):
        p = ResumeParser(FULL_RESUME).parse()
        assert "PyTorch" in p.experiences[0].description

    def test_no_experience_section(self):
        p = ResumeParser(MINIMAL_RESUME).parse()
        assert p.experiences == []

    def test_alternate_section_name(self):
        p = ResumeParser(CV_HEADER_RESUME).parse()
        assert len(p.experiences) >= 1
        assert p.experiences[0].title == "Frontend Developer"

    def test_tools_extraction(self):
        p = ResumeParser(FULL_RESUME).parse()
        tools = p.experiences[0].tools
        assert "NLP" in tools or "PyTorch" in tools


class TestEducationExtraction:
    def test_basic_education(self):
        p = ResumeParser(FULL_RESUME).parse()
        assert len(p.education) >= 1
        assert p.education[0].institution == "State University"

    def test_degree_detection(self):
        p = ResumeParser(FULL_RESUME).parse()
        assert "Bachelor" in p.education[0].degree

    def test_graduation_year(self):
        p = ResumeParser(FULL_RESUME).parse()
        assert "2018" in p.education[0].graduation

    def test_no_education(self):
        p = ResumeParser(MINIMAL_RESUME).parse()
        assert p.education == []


class TestSummaryExtraction:
    def test_summary(self):
        p = ResumeParser(FULL_RESUME).parse()
        assert "machine learning" in p.summary.lower()

    def test_empty_resume_summary(self):
        p = ResumeParser(MINIMAL_RESUME).parse()
        # Should still produce something (the name/contact lines fall through)
        assert isinstance(p.summary, str)


class TestSectionExtraction:
    def test_certifications(self):
        p = ResumeParser(FULL_RESUME).parse()
        assert len(p.certifications) >= 1

    def test_achievements(self):
        p = ResumeParser(FULL_RESUME).parse()
        assert len(p.achievements) >= 1


class TestEdgeCases:
    def test_empty_string(self):
        p = ResumeParser("").parse()
        assert p.contact.name == ""
        assert p.skills == []
        assert p.experiences == []

    def test_whitespace_only(self):
        p = ResumeParser("   \n\n   \n").parse()
        assert p.contact.name == ""

    def test_single_line(self):
        p = ResumeParser("Just a name").parse()
        assert p.contact.name == "Just a name"

    def test_resume_header_skipped(self):
        text = "Resume\nJohn Doe\njohn@test.com\n"
        p = ResumeParser(text).parse()
        assert p.contact.name == "John Doe"
