from urllib.parse import urlparse
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import requests

GITHUB_API_BASE_URL = "https://api.github.com"


class GitHubAPIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        rate_limited: bool = False,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.rate_limited = rate_limited


def parse_github_url(url: str) -> Tuple[str, str]:
    """Return owner and repo from a GitHub HTTPS URL."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "github.com":
        raise ValueError(
            "URL must be a GitHub repository URL like https://github.com/user/repo"
        )

    parts = parsed.path.strip("/").split("/")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError("URL must include an owner and repository name.")

    owner = parts[0]
    repo = parts[1].removesuffix(".git")
    if not repo:
        raise ValueError("URL must include an owner and repository name.")

    return owner, repo


def github_get(path: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Make an unauthenticated GitHub API GET request."""
    try:
        response = requests.get(f"{GITHUB_API_BASE_URL}{path}", timeout=10)
    except requests.RequestException as error:
        raise GitHubAPIError("Could not connect to GitHub.") from error

    if response.status_code == 200:
        return response.json()

    rate_limited = (
        response.status_code == 403
        and response.headers.get("x-ratelimit-remaining") == "0"
    )
    if rate_limited:
        raise GitHubAPIError(
            "GitHub API rate limit exceeded. Try again later.",
            status_code=response.status_code,
            rate_limited=True,
        )

    if response.status_code == 404:
        raise GitHubAPIError("Not found.", status_code=response.status_code)

    raise GitHubAPIError(
        f"GitHub returned unexpected status code {response.status_code}.",
        status_code=response.status_code,
    )


def get_repo_metadata(owner: str, repo: str) -> Dict[str, Any]:
    """Return repository metadata from the GitHub API."""
    data = github_get(f"/repos/{owner}/{repo}")
    if not isinstance(data, dict):
        raise GitHubAPIError("GitHub returned an unexpected repository response.")
    return data


def get_root_files(owner: str, repo: str) -> Set[str]:
    """Return root file and folder names for a repository."""
    data = github_get(f"/repos/{owner}/{repo}/contents")
    if not isinstance(data, list):
        raise GitHubAPIError("GitHub returned an unexpected contents response.")
    return {item["name"] for item in data if isinstance(item, dict) and "name" in item}


def get_commit_count_sample(owner: str, repo: str) -> int:
    """Return how many commits GitHub returned when asking for up to two."""
    data = github_get(f"/repos/{owner}/{repo}/commits?per_page=2")
    if not isinstance(data, list):
        raise GitHubAPIError("GitHub returned an unexpected commits response.")
    return len(data)
