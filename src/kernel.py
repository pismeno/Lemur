from werkzeug.wrappers import Request, Response
from routing import dispatch_request

def application(environ, start_response):
    request = Request(environ)
    
    result = dispatch_request(request)
    
    if isinstance(result, Response):
        response = result
    else:
        response = Response(result, mimetype='text/html')
        
    return response(environ, start_response)