from pathlib import Path
from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import HTTPException

from lemur.responses import make_spa_app_res

__url_map = Map()
__route_functions = {}

def add_route(url: str, name: str, function):
    __url_map.add(Rule(url, endpoint=name))
    __route_functions[name] = function

def mount_spa(url_prefix: str, name: str, app_directory: str):
    clean_prefix = url_prefix.rstrip('/')
    
    __url_map.add(Rule(f"{clean_prefix}", endpoint=name))
    __url_map.add(Rule(f"{clean_prefix}/", endpoint=name))
    
    __url_map.add(Rule(f"{clean_prefix}/<path:subpath>", endpoint=name))

    base_dir = Path(app_directory)

    def spa_dispatcher(request):
        raw_subpath = request.path.removeprefix(clean_prefix)
        safe_subpath = raw_subpath.lstrip('/')
        
        actual_path = base_dir / safe_subpath
        return make_spa_app_res(str(actual_path))
    
    __route_functions[name] = spa_dispatcher

def dispatch_request(request: Request) -> Response:
    adapter = __url_map.bind_to_environ(request.environ)
    try:
        endpoint, url_vars = adapter.match()
        dispatch_function = __route_functions[endpoint]

        return dispatch_function(request)
    except HTTPException as e:
            return e