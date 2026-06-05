import typer
from rich.console import Console

app = typer.Typer()
console = Console()


@app.command()
def audit(url: str):
    """Audit a GitHub repository for project-readiness."""
    console.print("[bold]RepoReady Audit Report[/bold]")
    console.print(f"Repository: {url}")
    console.print()
    console.print("✅ CLI is working")


@app.command()
def version():
    """Show the RepoReady version."""
    console.print("RepoReady 0.1.0")


if __name__ == "__main__":
    app()