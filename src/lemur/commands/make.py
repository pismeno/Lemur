import typer

from lemur.utils.assets import PRIVATE_PATH

def run(
    what: str = typer.Argument(default=..., help="What to make", show_default=False),
    name: str = typer.Argument(default=..., help="Name of the thing to make", show_default=False)
):
    """Make a new view, or route."""
    match what:
        case "view":
            __make_view_file(name)
        case "tail":
            __make_view_file(name)
        case "route":
            __make_routing_file(name)
        case "router":
            __make_routing_file(name)
        case _:
            print(f"Error: Unknown thing to make: '{what}'")
            

def __make_routing_file(name: str):
    file_name = name if name.endswith(".py") else name + ".py"

    try:
        with open(file_name, "x", encoding="utf-8") as file:
            file.write("from lemur.routing import add_route\n")
        print(f"Routing file '{file_name}' created successfully.")
    except FileExistsError:
        print(f"Error: The file '{file_name}' already exists!")

def __make_view_file(name: str):
    file_name = name if name.endswith(".tail") else name + ".tail"

    try:
        with open(file_name, "x", encoding="utf-8") as file:
            pass
        print(f"View '{file_name}' created successfully.")
    except FileExistsError:
        print(f"Error: The file '{file_name}' already exists!")