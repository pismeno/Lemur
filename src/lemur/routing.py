import mimetypes
import inspect
import uuid
import re

from pathlib import Path
from typing import Callable

from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Request as WerkzeugRequest
from werkzeug.wrappers import Response as WerkzeugResponse
from werkzeug.exceptions import HTTPException as WerkzeugHTTPException

from lemur.utils.assets import PRIVATE_PATH
from lemur.wrappers import make_lemur_request
from lemur.wrappers import Request as LemurRequest
from lemur.wrappers import Response as LemurResponse
from lemur.exceptions import HTTPException as LemurHTTPException

from lemur.responses import make_error_view_res, make_file_content_res, make_json_res

__url_map = Map()
__route_functions = {}

__RULE_REGEX = re.compile(r'''
    <
    (?:
        (?P<converter>[a-zA-Z_][a-zA-Z0-9_]*)   # converter name
        (?:\((?P<args>.*?)\))?                  # converter arguments
        \:                                      # delimiter
    )?
    (?P<variable>[a-zA-Z_][a-zA-Z0-9_]*)        # variable name
    >
''', re.VERBOSE)

__CONVERTER_TYPES = {
    'int': int,
    'float': float,
    'string': str, # Werkzeug uses 'default' when no converter is specified
    'default': str,
    'path': str,
    'any': str,
    'uuid': uuid.UUID
}

def add_route(
    url: str,
    name: str, 
    function: Callable[[LemurRequest], LemurResponse], 
    methods: list[str] = None
) -> None:

    if methods is None:
        methods = ["GET"]
        
    try:
        sig = inspect.signature(function)
    except (ValueError, TypeError):
        raise TypeError(f"The provided handler for '{name}' must be a callable function.")

    params = list(sig.parameters.values())

    if not params:
        raise ValueError(
            f"Route handler '{function.__name__}' for '{name}' is invalid. "
            f"It must accept at least one positional argument for the 'LemurRequest'."
        )

    first_param = params[0]

    if first_param.kind == inspect.Parameter.KEYWORD_ONLY:
        raise ValueError(
            f"Route handler '{function.__name__}' for '{name}' is invalid. "
            f"The first argument '{first_param.name}' cannot be keyword-only; "
            f"it must accept a positional 'LemurRequest'."
        )

    if first_param.annotation != inspect.Parameter.empty:
        if first_param.annotation not in (LemurRequest, "LemurRequest"):
            raise TypeError(
                f"Route handler '{function.__name__}' first argument '{first_param.name}' "
                f"is type-hinted as '{first_param.annotation}', but it must be 'LemurRequest'."
            )
            
    url_vars = {}
    for match in __RULE_REGEX.finditer(url):
        var_name = match.group('variable')
        converter = match.group('converter') or 'default'
        url_vars[var_name] = converter
            
    handler_params = {p.name: p for p in params[1:]}
    has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params)

    for param_name, param in handler_params.items():
        if param.default == inspect.Parameter.empty and param.kind != inspect.Parameter.VAR_KEYWORD:
            if param_name not in url_vars:
                raise ValueError(
                    f"Route '{name}' handler requires argument '{param_name}', "
                    f"but it is missing from the URL rule '{url}'."
                )

    if not has_kwargs:
        for var_name in url_vars:
            if var_name not in handler_params:
                raise ValueError(
                    f"URL rule '{url}' provides variable '{var_name}', "
                    f"but the handler '{function.__name__}' does not accept it."
                )

    for var_name, converter_name in url_vars.items():
        if var_name in handler_params:
            param = handler_params[var_name]
            
            if param.annotation != inspect.Parameter.empty:
                expected_type = __CONVERTER_TYPES.get(converter_name, str)
                
                if param.annotation not in (expected_type, expected_type.__name__):
                    actual_type_name = getattr(param.annotation, '__name__', str(param.annotation))
                    raise TypeError(
                        f"Type mismatch in route '{name}' for variable '{var_name}'. "
                        f"URL converter '{converter_name}' expects '{expected_type.__name__}', "
                        f"but handler specifies '{actual_type_name}'."
                    )
        
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
        
        signature = inspect.signature(dispatch_function)
        params = list(signature.parameters.values())

        positional_args = []
        keyword_args = {}

        lemur_request = make_lemur_request(request)

        # enforce that the very first parameter gets the lemur_request
        first_param_name = params[0].name
        positional_args.append(lemur_request)
        kwargs.pop(first_param_name, None)

        for param in params[1:]:
            if param.name in kwargs:
                keyword_args[param.name] = kwargs[param.name]

        return dispatch_function(*positional_args, **keyword_args)
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