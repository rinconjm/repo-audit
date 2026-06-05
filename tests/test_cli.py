import unittest
from unittest.mock import patch

from typer.testing import CliRunner

from tests import _path  # noqa: F401
from repo_ready.audit import CheckResult, CheckStatus
from repo_ready.cli import app


class AuditCliTests(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch(
        "repo_ready.cli.audit_repository",
        return_value=[
            CheckResult("Repo exists", CheckStatus.PASS, "Found user/repo"),
            CheckResult("Multiple commits", CheckStatus.WARN, "Only 1 commit found"),
            CheckResult("uv.lock exists", CheckStatus.FAIL, "Missing uv.lock"),
        ],
    )
    def test_audit_prints_summary(self, mock_audit_repository):
        result = self.runner.invoke(
            app, ["audit", "https://github.com/user/repo"]
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Score: 1/3 checks passed", result.stdout)
        self.assertIn("Warnings: 1", result.stdout)
        self.assertIn("Failures: 1", result.stdout)
        mock_audit_repository.assert_called_once_with(
            "https://github.com/user/repo", strict=False
        )

    @patch(
        "repo_ready.cli.audit_repository",
        return_value=[
            CheckResult("Repo exists", CheckStatus.PASS, "Found user/repo"),
            CheckResult("Multiple commits", CheckStatus.WARN, "Only 1 commit found"),
        ],
    )
    def test_audit_strict_treats_warnings_as_failures_in_summary(
        self, mock_audit_repository
    ):
        result = self.runner.invoke(
            app, ["audit", "https://github.com/user/repo", "--strict"]
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Score: 1/2 checks passed", result.stdout)
        self.assertIn("Warnings: 1 treated as failure because --strict was used.", result.stdout)
        self.assertIn("Failures: 1", result.stdout)
        mock_audit_repository.assert_called_once_with(
            "https://github.com/user/repo", strict=True
        )


if __name__ == "__main__":
    unittest.main()
