import os
import importlib.util
from pathlib import Path
from werkzeug.wrappers import Request
from lemur.routing import dispatch_request

def application(environ, start_response):
    request = Request(environ)
    
    response = dispatch_request(request)
        
    return response(environ, start_response)

def boot_routes():
    project_root = Path(os.getcwd())
    routes_dir = project_root / "routes"

    if not routes_dir.exists() or not routes_dir.is_dir():
        return

    for file_path in routes_dir.glob("*.py"):
        if file_path.name == "__init__.py":
            continue

        module_name = f"routes.{file_path.stem}"

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)


boot_routes()