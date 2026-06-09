import typer

app = typer.Typer()

@app.command()
def check(path: str) -> None:
    """Check a resume PDF for ATS compatibility."""
    print(f"Checking {path}...")

if __name__ == "__main__":
    app()
