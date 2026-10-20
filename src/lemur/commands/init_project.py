import shutil
from pathlib import Path
from typing import Optional
import typer

from lemur.utils.assets import PROJECT_ROOT_PATH

def run(
    project_name: Optional[str] = typer.Argument(
        default=None,
        help="Name of the project. If omitted, initializes in the current directory.",
        show_default=False,
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing files without prompting"
    ),
):
    """Initialize a new Lemur project."""
    target_dir = PROJECT_ROOT_PATH / project_name if project_name else PROJECT_ROOT_PATH

    if project_name and target_dir.exists():
        typer.secho(f"Directory '{target_dir}' already exists.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if not project_name and target_dir.exists():
        has_files = any(target_dir.iterdir())
        if has_files and not force:
            typer.secho(f"Warning: '{target_dir}' is not empty.", fg=typer.colors.YELLOW)
            confirmed = typer.confirm(
                "Do you want to initialize the project here anyway? Files may be overwritten."
            )
            if not confirmed:
                typer.secho("Initialization aborted.", fg=typer.colors.RED)
                raise typer.Exit(code=0)

    template_dir = Path(__file__).parent.parent / "project_template"

    try:
        shutil.copytree(template_dir, target_dir, dirs_exist_ok=True)

        (target_dir / "public").mkdir(parents=True, exist_ok=True)
        (target_dir / "private").mkdir(parents=True, exist_ok=True)

        display_name = project_name or target_dir.name
        typer.secho(
            f"Project '{display_name}' initialized successfully at '{target_dir}'.",
            fg=typer.colors.GREEN,
        )
    except Exception as e:
        typer.secho(f"Error initializing project: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)