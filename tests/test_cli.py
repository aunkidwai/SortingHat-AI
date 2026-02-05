import sys
import pytest
from pathlib import Path
from unittest.mock import patch

from sortinghat.cli import main, read_text, build_arg_parser


@pytest.fixture
def resume_file(tmp_path):
    f = tmp_path / "resume.txt"
    f.write_text(
        "Jane Doe\njane@test.com\nSkills: Python, Docker\n"
        "Experience\nDeveloper\nAcme\nBuilt systems with Python.\n"
        "Education\nMIT\n",
        encoding="utf-8",
    )
    return f


@pytest.fixture
def jd_file(tmp_path):
    f = tmp_path / "jd.txt"
    f.write_text("Looking for a Python developer with Docker experience.", encoding="utf-8")
    return f


class TestReadText:
    def test_reads_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world", encoding="utf-8")
        assert read_text(f) == "hello world"

    def test_missing_file_exits(self, tmp_path):
        with pytest.raises(SystemExit):
            read_text(tmp_path / "nonexistent.txt")

    def test_directory_exits(self, tmp_path):
        with pytest.raises(SystemExit):
            read_text(tmp_path)


class TestBuildArgParser:
    def test_basic_args(self):
        parser = build_arg_parser()
        args = parser.parse_args(["resume.txt", "jd.txt"])
        assert args.resume == Path("resume.txt")
        assert args.job_description == Path("jd.txt")

    def test_optional_flags(self):
        parser = build_arg_parser()
        args = parser.parse_args([
            "resume.txt", "jd.txt",
            "--required", "Python", "Docker",
            "--optional", "AWS",
            "--llm", "--verbose",
        ])
        assert args.required == ["Python", "Docker"]
        assert args.optional == ["AWS"]
        assert args.llm is True
        assert args.verbose is True

    def test_default_model(self):
        parser = build_arg_parser()
        args = parser.parse_args(["resume.txt", "jd.txt"])
        assert args.model == "codellama:34b"


class TestMainFunction:
    def test_runs_successfully(self, resume_file, jd_file, capsys):
        result = main([
            str(resume_file),
            str(jd_file),
            "--required", "Python", "Docker",
        ])
        assert result == 0
        captured = capsys.readouterr()
        assert "Candidate Profile:" in captured.out
        assert "Score Breakdown:" in captured.out
        assert "Recommendations:" in captured.out

    def test_output_contains_skills(self, resume_file, jd_file, capsys):
        main([str(resume_file), str(jd_file), "--required", "Python"])
        captured = capsys.readouterr()
        assert "python" in captured.out.lower()

    def test_missing_resume_exits(self, jd_file):
        with pytest.raises(SystemExit):
            main(["/nonexistent/resume.txt", str(jd_file)])

    def test_verbose_flag(self, resume_file, jd_file, capsys):
        result = main([str(resume_file), str(jd_file), "--required", "Python", "-v"])
        assert result == 0
