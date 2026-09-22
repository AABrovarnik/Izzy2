---
name: project-reporting
description: Prepare repository-grounded project review reports and keep them in the project's doc directory with an explicit approval workflow.
---

# Project Reporting

Use this skill when reviewing a repository, recording technical findings, or preparing a report for discussion.

## Repository convention

- Store working reports in the repository's `doc/` directory.
- Use Markdown (`.md`) by default. Use another format only when the user or project requires it.
- Store approved/final documents in `approvedDoc/` only after explicit user approval; do not infer approval from creating or publishing a draft.
- Preserve existing documents and naming conventions. If `doc/` or `approvedDoc/` is absent, create it only when the report workflow requires it.

## Review workflow

1. Inspect repository instructions, status, entry points, build/test commands, configuration, deployment files, and existing documentation.
2. Separate observed facts from assumptions. Include commit/branch and review date when available.
3. Report findings by severity, with file/line references where practical, impact, and a concrete remediation.
4. Record what was verified and what could not be verified. Never claim tests passed when the required tool or environment was unavailable.
5. Keep the report suitable for discussion: include strengths, risks, recommended order of work, and an explicit conclusion.
6. Publish or move the document only when that external action is within the user's request. Treat the report as draft until the user explicitly approves it.

## File format

The default output is `doc/<descriptive-name>.md`. If a different format is requested, keep the same evidence, severity, verification, and approval semantics.
