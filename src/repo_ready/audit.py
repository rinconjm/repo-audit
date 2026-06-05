from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Set

from repo_ready.github import (
    GitHubAPIError,
    get_commit_count_sample,
    get_repo_metadata,
    get_root_files,
    parse_github_url,
)


class CheckStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    message: str


@dataclass
class AuditSummary:
    total: int
    passed: int
    warnings: int
    failures: int
    strict: bool = False


def calculate_summary(
    results: List[CheckResult], strict: bool = False
) -> AuditSummary:
    """Calculate score and status totals for an audit report."""
    passed = sum(result.status == CheckStatus.PASS for result in results)
    warnings = sum(result.status == CheckStatus.WARN for result in results)
    failures = sum(result.status == CheckStatus.FAIL for result in results)

    if strict:
        failures += warnings

    return AuditSummary(
        total=len(results),
        passed=passed,
        warnings=warnings,
        failures=failures,
        strict=strict,
    )


def check_repo_exists(url: str) -> CheckResult:
    """Check if a Github repository exists"""
    try:
        owner, repo = parse_github_url(url)
    except ValueError as error:
        return CheckResult(
            name="Repo exists",
            status=CheckStatus.FAIL,
            message=str(error),
        )

    try:
        get_repo_metadata(owner, repo)
        return CheckResult(
            name="Repo exists",
            status=CheckStatus.PASS,
            message=f"Found {owner}/{repo}",
        )
    except GitHubAPIError as error:
        if error.status_code == 404:
            return CheckResult(
                name="Repo exists",
                status=CheckStatus.FAIL,
                message=f"Repository {owner}/{repo} was not found",
            )
        return CheckResult(
            name="Repo exists",
            status=CheckStatus.WARN,
            message=str(error),
        )


def check_repo_public(metadata: Dict[str, Any]) -> CheckResult:
    """Check whether repository metadata describes a public repository."""
    if metadata.get("private"):
        return CheckResult(
            name="Repo is public",
            status=CheckStatus.FAIL,
            message="Repository is private",
        )

    return CheckResult(
        name="Repo is public",
        status=CheckStatus.PASS,
        message="Repository is public",
    )


def check_readme_exists(root_files: Set[str]) -> CheckResult:
    """Check whether the root contains a recognized README file."""
    candidates = ("README.md", "README.rst", "README.txt", "README")
    for candidate in candidates:
        if candidate in root_files:
            return CheckResult(
                name="README exists",
                status=CheckStatus.PASS,
                message=f"Found {candidate}",
            )

    return CheckResult(
        name="README exists",
        status=CheckStatus.FAIL,
        message="Missing README",
    )


def check_required_file(root_files: Set[str], filename: str) -> CheckResult:
    """Check whether a required root file exists."""
    if filename in root_files:
        return CheckResult(
            name=f"{filename} exists",
            status=CheckStatus.PASS,
            message=f"Found {filename}",
        )

    return CheckResult(
        name=f"{filename} exists",
        status=CheckStatus.FAIL,
        message=f"Missing {filename}",
    )


def check_multiple_commits(owner: str, repo: str) -> CheckResult:
    """Check whether a repository has at least two commits."""
    try:
        count = get_commit_count_sample(owner, repo)
    except GitHubAPIError as error:
        return CheckResult(
            name="Multiple commits",
            status=CheckStatus.WARN if error.rate_limited else CheckStatus.FAIL,
            message=str(error),
        )

    if count >= 2:
        return CheckResult(
            name="Multiple commits",
            status=CheckStatus.PASS,
            message="Found multiple commits",
        )

    if count == 1:
        return CheckResult(
            name="Multiple commits",
            status=CheckStatus.WARN,
            message="Only 1 commit found",
        )

    return CheckResult(
        name="Multiple commits",
        status=CheckStatus.FAIL,
        message="No commits found",
    )


def audit_repository(url: str, strict: bool = False) -> List[CheckResult]:
    """Run all RepoReady checks and return result rows."""
    del strict
    try:
        owner, repo = parse_github_url(url)
    except ValueError as error:
        return [
            CheckResult(
                name="Repo exists",
                status=CheckStatus.FAIL,
                message=str(error),
            )
        ]

    try:
        metadata = get_repo_metadata(owner, repo)
    except GitHubAPIError as error:
        status = CheckStatus.FAIL if error.status_code == 404 else CheckStatus.WARN
        message = (
            f"Repository {owner}/{repo} was not found"
            if error.status_code == 404
            else str(error)
        )
        return [CheckResult("Repo exists", status, message)]

    results = [
        CheckResult("Repo exists", CheckStatus.PASS, f"Found {owner}/{repo}"),
        check_repo_public(metadata),
    ]

    try:
        root_files = get_root_files(owner, repo)
    except GitHubAPIError as error:
        status = CheckStatus.WARN if error.rate_limited else CheckStatus.FAIL
        results.extend(
            [
                CheckResult("README exists", status, str(error)),
                CheckResult("pyproject.toml exists", status, str(error)),
                CheckResult("uv.lock exists", status, str(error)),
                CheckResult(".gitignore exists", status, str(error)),
            ]
        )
    else:
        results.extend(
            [
                check_readme_exists(root_files),
                check_required_file(root_files, "pyproject.toml"),
                check_required_file(root_files, "uv.lock"),
                check_required_file(root_files, ".gitignore"),
            ]
        )

    results.append(check_multiple_commits(owner, repo))
    return results
