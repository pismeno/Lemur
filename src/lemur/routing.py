from pathlib import Path
from typing import Callable

from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Request as WerkzeugRequest
from werkzeug.wrappers import Response as WerkzeugResponse
from werkzeug.exceptions import HTTPException as WerkzeugHTTPException

from lemur.wrappers import make_lemur_request
from lemur.wrappers import Request as LemurRequest
from lemur.wrappers import Response as LemurResponse
from lemur.wrappers import HTTPException as LemurHTTPException

from lemur.responses import make_spa_app_res
from lemur.responses import make_error_view_res
from lemur.responses import make_file_content_res
from lemur.responses import make_json_res

__url_map = Map()
__route_functions = {}

def add_route(
        url: str,
        name: str, 
        function: Callable[[LemurRequest], LemurResponse], 
        methods: list[str] = None
        ) -> None:
    
    if methods is None:
        methods = ["GET"]
        
    __url_map.add(Rule(url, endpoint=name, methods=methods, strict_slashes=False))
    __route_functions[name] = function

def mount_spa(
        url_prefix: str, 
        name: str, 
        app_directory: str
        ) -> None:
    
    clean_prefix = url_prefix.rstrip('/')
    
    __url_map.add(Rule(f"{clean_prefix}", endpoint=name))
    __url_map.add(Rule(f"{clean_prefix}/", endpoint=name))
    __url_map.add(Rule(f"{clean_prefix}/<path:subpath>", endpoint=name))

    def spa_dispatcher(request: WerkzeugRequest, subpath: str = ""):
        safe_subpath = subpath.lstrip('/')
        
        if safe_subpath:
            full_target = f"{app_directory}/{safe_subpath}"
        else:
            full_target = app_directory
            
        return make_spa_app_res(full_target)
    
    __route_functions[name] = spa_dispatcher


def dispatch_request(request: WerkzeugRequest) -> WerkzeugResponse:
    if request.path.startswith("/public/"):
        file_path = request.path.removeprefix("/public/")
        return make_file_content_res(file_path, private=False)

    adapter = __url_map.bind_to_environ(request.environ)
    
    try:
        endpoint, __build_class__ = adapter.match()
        
        dispatch_function = __route_functions.get(endpoint)

        if not dispatch_function:
            return _abort_internal_server_error(request)
        
        lemur_request = make_lemur_request(request)
        return dispatch_function(lemur_request)
    except WerkzeugHTTPException as e:
        print(f"Error during request dispatch: {e}")
        lemur_exception = LemurHTTPException(e.code, e.description)
        return _abort(lemur_exception, request)
        
    except Exception as e:
        print(f"Error during request dispatch: {e}")
        return _abort_internal_server_error(request)


def _abort_internal_server_error(request: WerkzeugRequest) -> WerkzeugResponse:
    return _abort(LemurHTTPException(500, "Internal server error"), request)
    
def _abort(lemur_exception: LemurHTTPException, request: WerkzeugRequest) -> WerkzeugResponse:
    if __expects_json(request):
        return make_json_res({"message": lemur_exception.message}, status=lemur_exception.status_code)
    else:
        return make_error_view_res(lemur_exception)

def __expects_json(req: WerkzeugRequest) -> bool:
    """Helper to determine if the client expects a JSON response."""
    best = req.accept_mimetypes.best_match(['application/json', 'text/html'])
    if best == 'application/json':
        return True
    if req.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return True
    return False