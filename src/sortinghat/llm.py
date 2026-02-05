from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "codellama:34b"
DEFAULT_BASE_URL = "http://localhost:11434"


@dataclass
class LLMResponse:
    text: str
    model: str
    done: bool


class OllamaClient:
    """Lightweight client for a local Ollama instance (no external deps)."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 120,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def is_available(self) -> bool:
        """Check if the Ollama server is reachable."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5):
                return True
        except (urllib.error.URLError, OSError):
            logger.debug("Ollama server not reachable at %s", self.base_url)
            return False

    def generate(self, prompt: str, system: str | None = None) -> LLMResponse:
        """Send a generation request to Ollama and return the full response."""
        payload: dict = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return LLMResponse(
                    text=body.get("response", ""),
                    model=body.get("model", self.model),
                    done=body.get("done", True),
                )
        except (urllib.error.URLError, OSError) as exc:
            logger.error("Ollama request failed: %s", exc)
            raise ConnectionError(f"Failed to reach Ollama at {self.base_url}: {exc}") from exc

    def enhance_recommendations(
        self,
        resume_summary: str,
        skills: list[str],
        missing_skills: list[str],
        job_description: str,
        score: float,
    ) -> str:
        """Use the LLM to generate tailored resume improvement recommendations."""
        system_prompt = (
            "You are a professional career coach and resume expert. "
            "Provide specific, actionable resume improvement recommendations. "
            "Be concise — return 3-5 bullet points. "
            "Never invent qualifications the candidate does not have."
        )
        prompt = (
            f"## Candidate Summary\n{resume_summary}\n\n"
            f"## Current Skills\n{', '.join(skills)}\n\n"
            f"## Missing Required Skills\n{', '.join(missing_skills) if missing_skills else 'None'}\n\n"
            f"## Job Description\n{job_description}\n\n"
            f"## Match Score\n{score}%\n\n"
            "Based on this analysis, provide specific recommendations to improve this resume "
            "for the target role. Focus on actionable steps."
        )
        response = self.generate(prompt, system=system_prompt)
        return response.text

    def extract_skills_from_jd(self, job_description: str) -> dict[str, list[str]]:
        """Use the LLM to extract required and optional skills from a job description."""
        system_prompt = (
            "You are a technical recruiter. Extract skills from the job description. "
            "Return ONLY valid JSON with two keys: \"required\" and \"optional\", "
            "each mapping to a list of skill strings. No other text."
        )
        response = self.generate(job_description, system=system_prompt)
        try:
            result = json.loads(response.text)
            return {
                "required": result.get("required", []),
                "optional": result.get("optional", []),
            }
        except (json.JSONDecodeError, AttributeError):
            logger.warning("LLM did not return valid JSON for skill extraction")
            return {"required": [], "optional": []}
