from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from .pipeline import ResumePipeline

logger = logging.getLogger(__name__)


def read_text(path: Path) -> str:
    if not path.exists():
        logger.error("File not found: %s", path)
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    if not path.is_file():
        logger.error("Not a file: %s", path)
        print(f"Error: not a regular file: {path}", file=sys.stderr)
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse and score a resume against a job description.")
    parser.add_argument("resume", type=Path, help="Path to resume file (txt, pdf, docx)")
    parser.add_argument("job_description", type=Path, help="Path to job description text file")
    parser.add_argument("--required", nargs="*", default=None, help="Explicit required skills")
    parser.add_argument("--optional", nargs="*", default=None, help="Optional skills")
    parser.add_argument(
        "--llm",
        action="store_true",
        default=False,
        help="Enable Ollama LLM for enhanced recommendations",
    )
    parser.add_argument(
        "--model",
        default="codellama:34b",
        help="Ollama model to use (default: codellama:34b)",
    )
    parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434",
        help="Ollama server URL (default: http://localhost:11434)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose (debug) logging",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(name)s %(levelname)s: %(message)s",
    )

    resume_text = read_text(args.resume)
    jd_text = read_text(args.job_description)

    pipeline = ResumePipeline(
        jd_text,
        required_skills=args.required,
        optional_skills=args.optional,
        use_llm=args.llm,
        llm_model=args.model,
        llm_base_url=args.ollama_url,
    )
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
