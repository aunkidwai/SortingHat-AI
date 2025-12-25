from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from .pipeline import ResumePipeline


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse and score a resume against a job description.")
    parser.add_argument("resume", type=Path, help="Path to resume text file")
    parser.add_argument("job_description", type=Path, help="Path to job description text file")
    parser.add_argument("--required", nargs="*", default=None, help="Explicit required skills")
    parser.add_argument("--optional", nargs="*", default=None, help="Optional skills")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    resume_text = read_text(args.resume)
    jd_text = read_text(args.job_description)

    pipeline = ResumePipeline(jd_text, required_skills=args.required, optional_skills=args.optional)
    result = pipeline.run(resume_text)

    print("Candidate Profile:")
    print(f"  Name: {result.profile.contact.name}")
    print(f"  Email: {result.profile.contact.email}")
    print(f"  Skills: {', '.join(result.profile.normalized_skills())}")
    print("\nScore Breakdown:")
    print(f"  Required coverage: {result.breakdown.required_coverage}%")
    print(f"  Optional coverage: {result.breakdown.optional_coverage}%")
    print(f"  Experience alignment: {result.breakdown.experience_alignment}%")
    print(f"  Overall: {result.breakdown.overall_score}")
    print("\nRecommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
