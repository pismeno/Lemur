import shutil
from pathlib import Path
from typing import Optional
import typer
from typer import Typer

app = Typer(help="CLI tool to manage Lemur projects.")

@app.command()
def init(
    project_name: str = typer.Argument(
        default=...,
        help="Name of the project", 
        show_default=False
    )
):
    target_dir = Path.cwd() / project_name

    if target_dir.exists():
        typer.secho(f"Directory '{target_dir}' already exists.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    template_dir = Path(__file__).parent / "project_template"

    try:
        shutil.copytree(template_dir, target_dir)
        typer.secho(f"Project '{project_name}' initialized successfully at '{target_dir}'.", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"Error initializing project: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    
@app.command()
def run():
    """Start the local development server."""
    typer.echo("Starting server...")
    
if __name__ == "__main__":
    app()