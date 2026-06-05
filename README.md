# RepoReady

RepoReady is a command-line tool that audits a public GitHub repository for DSC
190 project submission readiness. It checks common final-project requirements
and prints a beginner-friendly terminal report with passes, warnings, failures,
and a final score.

RepoReady audits public repositories through the unauthenticated GitHub API. If
GitHub rate-limits the request, the tool reports a warning instead of crashing.

## Installation

Install dependencies and the local package with `uv`:

```bash
uv sync
uv build
uv pip install dist/repo_audit-0.1.0-py3-none-any.whl --reinstall
```

## Usage

Audit a public GitHub repository:

```bash
uv run --no-sync repoready audit https://github.com/user/repo
```

Treat warnings as failures in the summary:

```bash
uv run --no-sync repoready audit https://github.com/user/repo --strict
```

Show the installed version:

```bash
uv run --no-sync repoready version
```

Example output:

```text
RepoReady Audit Report
Repository: https://github.com/user/repo

✅ Repo exists: Found user/repo
✅ Repo is public: Repository is public
✅ README exists: Found README.md
✅ pyproject.toml exists: Found pyproject.toml
✅ uv.lock exists: Found uv.lock
✅ .gitignore exists: Found .gitignore
⚠️ Multiple commits: Only 1 commit found

Score: 6/7 checks passed
Warnings: 1
Failures: 0
```

## Checks

RepoReady version 1 checks:

- The GitHub repository URL is valid and the repository exists.
- The repository is public.
- The repository root includes a README file.
- The repository root includes `pyproject.toml`.
- The repository root includes `uv.lock`.
- The repository root includes `.gitignore`.
- The repository has at least two commits.
