import unittest
from unittest.mock import patch

from tests import _path  # noqa: F401
from repo_ready.audit import (
    CheckResult,
    CheckStatus,
    audit_repository,
    calculate_summary,
    check_multiple_commits,
    check_repo_public,
)


class CheckResultTests(unittest.TestCase):
    def test_check_result_tracks_pass_warn_and_fail_statuses(self):
        result = CheckResult(
            name="Multiple commits",
            status=CheckStatus.WARN,
            message="Only 1 commit found",
        )

        self.assertEqual(result.status, CheckStatus.WARN)
        self.assertEqual(result.status.value, "warn")


class SummaryTests(unittest.TestCase):
    def test_calculate_summary_counts_statuses_in_normal_mode(self):
        results = [
            CheckResult("Repo exists", CheckStatus.PASS, "Found user/repo"),
            CheckResult("Multiple commits", CheckStatus.WARN, "Only 1 commit found"),
            CheckResult("uv.lock exists", CheckStatus.FAIL, "Missing uv.lock"),
        ]

        summary = calculate_summary(results)

        self.assertEqual(summary.total, 3)
        self.assertEqual(summary.passed, 1)
        self.assertEqual(summary.warnings, 1)
        self.assertEqual(summary.failures, 1)

    def test_calculate_summary_treats_warnings_as_failures_in_strict_mode(self):
        results = [
            CheckResult("Repo exists", CheckStatus.PASS, "Found user/repo"),
            CheckResult("Multiple commits", CheckStatus.WARN, "Only 1 commit found"),
        ]

        summary = calculate_summary(results, strict=True)

        self.assertEqual(summary.total, 2)
        self.assertEqual(summary.passed, 1)
        self.assertEqual(summary.warnings, 1)
        self.assertEqual(summary.failures, 1)
        self.assertTrue(summary.strict)


class RepoPublicTests(unittest.TestCase):
    def test_public_repo_passes(self):
        result = check_repo_public({"private": False})

        self.assertEqual(result.status, CheckStatus.PASS)
        self.assertEqual(result.message, "Repository is public")

    def test_private_repo_fails(self):
        result = check_repo_public({"private": True})

        self.assertEqual(result.status, CheckStatus.FAIL)
        self.assertEqual(result.message, "Repository is private")


class MultipleCommitsTests(unittest.TestCase):
    @patch("repo_ready.audit.get_commit_count_sample", return_value=2)
    def test_multiple_commits_passes(self, mock_get_commit_count_sample):
        result = check_multiple_commits("user", "repo")

        self.assertEqual(result.status, CheckStatus.PASS)
        self.assertEqual(result.message, "Found multiple commits")
        mock_get_commit_count_sample.assert_called_once_with("user", "repo")

    @patch("repo_ready.audit.get_commit_count_sample", return_value=1)
    def test_single_commit_warns(self, mock_get_commit_count_sample):
        result = check_multiple_commits("user", "repo")

        self.assertEqual(result.status, CheckStatus.WARN)
        self.assertEqual(result.message, "Only 1 commit found")
        mock_get_commit_count_sample.assert_called_once_with("user", "repo")


class AuditRepositoryTests(unittest.TestCase):
    @patch("repo_ready.audit.get_commit_count_sample", return_value=2)
    @patch(
        "repo_ready.audit.get_root_files",
        return_value={"README.md", "pyproject.toml", "uv.lock", ".gitignore"},
    )
    @patch("repo_ready.audit.get_repo_metadata", return_value={"private": False})
    def test_audit_repository_returns_all_seven_checks(
        self,
        mock_get_repo_metadata,
        mock_get_root_files,
        mock_get_commit_count_sample,
    ):
        results = audit_repository("https://github.com/user/repo")

        self.assertEqual(len(results), 7)
        self.assertTrue(all(result.status == CheckStatus.PASS for result in results))
        self.assertEqual(
            [result.name for result in results],
            [
                "Repo exists",
                "Repo is public",
                "README exists",
                "pyproject.toml exists",
                "uv.lock exists",
                ".gitignore exists",
                "Multiple commits",
            ],
        )
        mock_get_repo_metadata.assert_called_once_with("user", "repo")
        mock_get_root_files.assert_called_once_with("user", "repo")
        mock_get_commit_count_sample.assert_called_once_with("user", "repo")


if __name__ == "__main__":
    unittest.main()
