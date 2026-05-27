from werkzeug.wrappers import Request, Response
from routing import dispatch_request

def application(environ, start_response):
    request = Request(environ)
    
    response = dispatch_request(request)
        
    return response(environ, start_response)