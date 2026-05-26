from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Request
from werkzeug.exceptions import HTTPException

__url_map = Map()
__route_functions = {}


def add_route(url: str, name: str, function):
    __url_map.add(Rule(url, endpoint=name))
    __route_functions[name] = function

def dispatch_request(request: Request):
    adapter = __url_map.bind_to_environ(request.environ)
    try:
        endpoint, url_vars = adapter.match()
        dispatch_function = __route_functions[endpoint]

        return dispatch_function(request)
    except HTTPException as e:
            return e