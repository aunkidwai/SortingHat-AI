from sortinghat.models import CandidateProfile, ContactInfo, Education, Experience


class TestContactInfo:
    def test_defaults(self):
        c = ContactInfo()
        assert c.name == ""
        assert c.email == ""
        assert c.phone == ""
        assert c.location == ""

    def test_merge_fills_gaps(self):
        a = ContactInfo(name="Alice", email="", phone="123", location="")
        b = ContactInfo(name="", email="alice@x.com", phone="", location="NYC")
        merged = a.merge(b)
        assert merged.name == "Alice"
        assert merged.email == "alice@x.com"
        assert merged.phone == "123"
        assert merged.location == "NYC"

    def test_merge_prefers_self(self):
        a = ContactInfo(name="Alice", email="a@a.com", phone="111", location="LA")
        b = ContactInfo(name="Bob", email="b@b.com", phone="222", location="NY")
        merged = a.merge(b)
        assert merged.name == "Alice"
        assert merged.email == "a@a.com"

    def test_merge_strips_whitespace(self):
        a = ContactInfo(name="  ", email="  a@a.com  ", phone="", location="")
        b = ContactInfo(name="Bob", email="", phone="", location="")
        merged = a.merge(b)
        assert merged.name == "Bob"
        assert merged.email == "a@a.com"


class TestExperience:
    def test_defaults(self):
        e = Experience(title="Dev", company="Co")
        assert e.description == ""
        assert e.duration == ""
        assert e.tools == []


class TestEducation:
    def test_defaults(self):
        e = Education(institution="MIT")
        assert e.degree == ""
        assert e.graduation == ""


class TestCandidateProfile:
    def test_empty_profile(self):
        p = CandidateProfile()
        assert p.normalized_skills() == []
        assert p.short_experience_highlights() == []

    def test_normalized_skills_deduplicates_and_sorts(self):
        p = CandidateProfile(skills=["Python", "python", "PYTHON", "Java", "java"])
        assert p.normalized_skills() == ["java", "python"]

    def test_normalized_skills_strips_whitespace(self):
        p = CandidateProfile(skills=["  Python  ", "", "  ", "Java"])
        assert p.normalized_skills() == ["java", "python"]

    def test_short_experience_highlights(self):
        p = CandidateProfile(
            experiences=[
                Experience(title="Dev", company="Co", description="Built stuff"),
                Experience(title="Lead", company="Inc"),
            ]
        )
        highlights = p.short_experience_highlights()
        assert len(highlights) == 2
        assert "Dev at Co: Built stuff" == highlights[0]
        assert "Lead at Inc" == highlights[1]
