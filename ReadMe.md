# SortingHat AI: Resume Parsing and Personalization System

SortingHat AI is an advanced LLM-based, multi-agent, multi-modal retrieval-augmented generation (RAG) platform that parses resumes, normalizes candidate profiles into structured data, and generates personalized, job-aligned resume improvements. The platform supports applicant-facing guidance and recruiter-facing workflows to improve matching accuracy and throughput.

## Business Problem

Hiring pipelines often fail due to inconsistent resume formats, ambiguous skill signals, manual screening constraints, and generic resumes that are not tailored to role requirements. SortingHat AI addresses these challenges through robust extraction, structured candidate representations, and retrieval-grounded LLM reasoning for explainable matching and personalization.

## Core Capabilities

### 1. Multi-Modal Resume Ingestion & Parsing
- Accepts PDF, DOCX, and image resumes with text + layout extraction.
- Extracts contact information, summaries, work experience, education, certifications, skills, tools/technologies, domains, seniority signals, and achievements.
- Produces a structured JSON resume schema suitable for ranking and analytics (e.g., `candidate_profile.json`).

### 2. Multi-Agent Orchestration
- **Ingestion Agent:** detects file type, quality, and parsing strategy.
- **Extraction Agent:** captures sections and entities into a structured schema.
- **Normalization Agent:** maps skills/titles to canonical forms, resolves duplicates, and tags seniority.
- **RAG Grounding Agent:** retrieves job requirements, skill ontology entries, and best-practice templates.
- **Rewrite Agent:** generates role-tailored bullets and summaries while preserving truthfulness.
- **ATS Compliance Agent:** enforces formatting constraints, keyword coverage, and readability.
- **Quality Assurance Agent:** validates completeness, detects contradictions, flags unverifiable claims, and enforces no-fabrication rules.

### 3. Retrieval-Augmented Generation for Job Alignment
- Grounds generation with job descriptions, curated skills taxonomy/ontology, role-specific bullet templates, and the candidate’s own experience.
- Produces personalization aligned to job requirements while remaining consistent with the candidate’s background.

### 4. Applicant Personalization
- Guided workflow: parse resume → ask targeted follow-up questions → generate tailored summaries, role-specific bullet rewrites, optimized skills sections, and project framing suggestions.
- Recommends roles based on skill similarity and experience signals, delivering revised resume drafts and recommendation reports.

### 5. Recruiter Workflows
- Batch and individual sorting against job descriptions.
- For each candidate: match score, evidence-based matching explanation, gap analysis, and shortlist recommendations with confidence levels.
- Reduces manual screening time and improves consistency across recruiters.

## Architecture Overview

1. **Ingestion Layer:** file intake, parsing, text/layout extraction.
2. **Structured Representation:** resume schema (JSON) and embeddings.
3. **Retrieval Layer:** vector store for job requirements, skill ontology, and templates.
4. **LLM Orchestration:** multi-agent graph with guardrails.
5. **Outputs:** applicant-focused resume improvements and recruiter-focused ranking + evidence reports.

### Key Design Principles
- **Truth-preserving generation:** never invent employers, dates, degrees, or achievements.
- **Explainable ranking:** outputs cite extracted resume evidence.
- **Separation of concerns:** extraction, rewriting, and compliance checks are isolated.

## Matching Logic & Scoring

- Must-have requirements: core skills, years of experience, location/work authorization when relevant.
- Role keywords and responsibilities: semantic similarity with embeddings and term coverage.
- Seniority signals: scope, leadership cues, project complexity, and impact metrics.
- Recency weighting: prioritizes recent skill and role alignment.
- Outputs include a match rationale, not just a score.

## Quality, Safety, and Guardrails

- Schema validation for completeness and format integrity.
- Contradiction checks for overlapping employment dates or inconsistent titles.
- Hallucination prevention: rewrite agent constrained to candidate-provided facts; improvements are framed as suggestions unless supported by the resume.
- PII handling with configurable redaction for recruiter exports and logs.

## Tech Stack (Suggested)

- **Models & Embeddings:** LLaMA, Hugging Face-hosted models.
- **Orchestration:** LangChain multi-agent workflows.
- **Data Handling:** Python ETL, parsers, evaluation scripts, and API services.
- **Storage/Retrieval:** Vector store for job descriptions, skill ontology, and templates.

## Resume-Style Outcomes

- Designed and implemented a multi-agent, multi-modal RAG pipeline to parse heterogeneous resumes into a validated structured schema and generate truth-preserving, role-aligned improvements.
- Built recruiter-grade batch screening with evidence-backed matching rationales and gap analysis to improve screening consistency and speed.
- Implemented ATS-aware rewriting and compliance checks to increase keyword coverage and readability without fabricating experience.

## Potential Enhancements

- Evaluation harness with labeled datasets to track extraction precision/recall and ranking metrics (MRR, nDCG).
- Human-in-the-loop review: recruiter feedback refines scoring weights and templates.
- Deployment: containerized API, async batch processing, and embedding caching.

