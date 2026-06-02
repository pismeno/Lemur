from pathlib import Path
from typing import Callable
import mimetypes

from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Request as WerkzeugRequest
from werkzeug.wrappers import Response as WerkzeugResponse
from werkzeug.exceptions import HTTPException as WerkzeugHTTPException

from lemur.utils.assets import PRIVATE_PATH
from lemur.wrappers import make_lemur_request
from lemur.wrappers import Request as LemurRequest
from lemur.wrappers import Response as LemurResponse
from lemur.exceptions import HTTPException as LemurHTTPException

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

    def spa_dispatcher(request: LemurRequest, subpath: str = ""):
        safe_subpath = subpath.lstrip('/')
        safe_app_dir = app_directory.strip('/')
        
        if safe_subpath:
            full_target = f"{safe_app_dir}/{safe_subpath}"
        else:
            full_target = safe_app_dir
            
        path_obj = Path(full_target)
        target_path = PRIVATE_PATH / path_obj

        if target_path.is_file():
            mimetype, _ = mimetypes.guess_type(target_path)
            
            if not mimetype:
                mimetype = 'application/octet-stream' 
                
            with open(target_path, 'rb') as file:
                return LemurResponse(file.read(), status=200, mimetype=mimetype)

        if target_path.suffix in ['.js', '.css', '.ico', '.json', '.map']:
            raise LemurHTTPException(404, f"Asset missing at physical path: {target_path}")

        index_path = PRIVATE_PATH / Path(safe_app_dir) / 'index.html'
        
        if index_path.is_file():
            with open(index_path, 'rb') as f:
                return LemurResponse(f.read(), status=200, mimetype='text/html')

        raise LemurHTTPException(404, f"SPA app not found at path: {full_target}")
    
    __route_functions[name] = spa_dispatcher


def dispatch_request(request: WerkzeugRequest) -> WerkzeugResponse:
    try:
        if request.path.startswith("/public/"):
            file_path = request.path.removeprefix("/public/")
            return make_file_content_res(file_path, private=False)
    
    except FileNotFoundError:
        _abort(LemurHTTPException(404, "Public asset not found"), request)
    except PermissionError:
        _abort(LemurHTTPException(403, "Access denied"), request)

    adapter = __url_map.bind_to_environ(request.environ)
    
    try:
        endpoint, kwargs = adapter.match()
        
        dispatch_function = __route_functions.get(endpoint)

        if not dispatch_function:
            return _abort_internal_server_error(request)
        
        lemur_request = make_lemur_request(request)
        return dispatch_function(lemur_request, **kwargs)
    except WerkzeugHTTPException as e:
        print(f"Error during request dispatch: {e}")
        lemur_exception = LemurHTTPException(e.code, e.description)
        return _abort(lemur_exception, request)
    
    except LemurHTTPException as e:
        print(f"Error during request dispatch: {e}")
        return _abort(e, request)
        
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