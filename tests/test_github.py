import unittest
from unittest.mock import Mock, patch

from tests import _path  # noqa: F401
from repo_ready.github import (
    GitHubAPIError,
    get_commit_count_sample,
    get_repo_metadata,
    get_root_files,
    parse_github_url,
)


class ParseGitHubUrlTests(unittest.TestCase):
    def test_parses_https_github_repository_url(self):
        self.assertEqual(
            parse_github_url("https://github.com/rinconjm/repo-audit"),
            ("rinconjm", "repo-audit"),
        )

    def test_parses_url_with_git_suffix(self):
        self.assertEqual(
            parse_github_url("https://github.com/rinconjm/repo-audit.git"),
            ("rinconjm", "repo-audit"),
        )

    def test_rejects_non_github_url(self):
        with self.assertRaisesRegex(ValueError, "GitHub repository URL"):
            parse_github_url("https://gitlab.com/rinconjm/repo-audit")

    def test_rejects_missing_scheme(self):
        with self.assertRaisesRegex(ValueError, "GitHub repository URL"):
            parse_github_url("github.com/rinconjm/repo-audit")

    def test_rejects_url_without_repo_name(self):
        with self.assertRaisesRegex(ValueError, "owner and repository"):
            parse_github_url("https://github.com/rinconjm")


class GitHubAPITests(unittest.TestCase):
    @patch("repo_ready.github.requests.get")
    def test_get_repo_metadata_returns_json_for_success(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=lambda: {"private": False})

        self.assertEqual(get_repo_metadata("user", "repo"), {"private": False})
        mock_get.assert_called_once()

    @patch("repo_ready.github.requests.get")
    def test_get_repo_metadata_raises_not_found_for_404(self, mock_get):
        mock_get.return_value = Mock(status_code=404, json=lambda: {})

        with self.assertRaises(GitHubAPIError) as context:
            get_repo_metadata("user", "repo")

        self.assertEqual(context.exception.status_code, 404)

    @patch("repo_ready.github.requests.get")
    def test_get_root_files_returns_root_names(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: [{"name": "README.md"}, {"name": "src"}],
        )

        self.assertEqual(get_root_files("user", "repo"), {"README.md", "src"})

    @patch("repo_ready.github.requests.get")
    def test_get_commit_count_sample_returns_up_to_two_commits(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: [{"sha": "abc"}, {"sha": "def"}],
        )

        self.assertEqual(get_commit_count_sample("user", "repo"), 2)


if __name__ == "__main__":
    unittest.main()
