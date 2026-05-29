import shutil
from pathlib import Path
import typer

from lemur.utils.assets import PROJECT_ROOT_PATH

def run(
    project_name: str = typer.Argument(default=..., help="Name of the project", show_default=False)
):
    """Initialize a new Lemur project."""
    target_dir = PROJECT_ROOT_PATH / project_name

    if target_dir.exists():
        typer.secho(f"Directory '{target_dir}' already exists.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    template_dir = Path(__file__).parent.parent / "project_template"

    try:
        shutil.copytree(template_dir, target_dir)
        typer.secho(f"Project '{project_name}' initialized successfully at '{target_dir}'.", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"Error initializing project: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)