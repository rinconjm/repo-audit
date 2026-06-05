import typer
from rich.console import Console

from repo_ready.audit import (
    CheckResult,
    CheckStatus,
    audit_repository,
    calculate_summary,
)

app = typer.Typer()
console = Console()


def print_check_result(result: CheckResult) -> None:
    symbols = {
        CheckStatus.PASS: "✅",
        CheckStatus.WARN: "⚠️",
        CheckStatus.FAIL: "❌",
    }
    console.print(f"{symbols[result.status]} {result.name}: {result.message}")


@app.command()
def audit(url: str, strict: bool = False):
    """Audit a GitHub repository for project-readiness."""
    console.print("[bold]RepoReady Audit Report[/bold]")
    console.print(f"Repository: {url}")
    console.print()

    results = audit_repository(url, strict=strict)
    for result in results:
        print_check_result(result)

    summary = calculate_summary(results, strict=strict)
    console.print()
    console.print(f"Score: {summary.passed}/{summary.total} checks passed")
    if summary.strict and summary.warnings:
        console.print(
            f"Warnings: {summary.warnings} treated as failure because --strict was used."
        )
    else:
        console.print(f"Warnings: {summary.warnings}")
    console.print(f"Failures: {summary.failures}")


@app.command()
def version():
    """Show the RepoReady version."""
    console.print("RepoReady 0.1.0")

if __name__ == "__main__":
    app()
