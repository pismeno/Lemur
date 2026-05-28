

from typer import Typer
import lemur.commands.init_project as init_project
import lemur.commands.serve as serve

app = Typer(help="CLI tool to manage Lemur projects.")

app.command(name="init")(init_project.run)
app.command(name="serve")(serve.run)