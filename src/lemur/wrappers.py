from dataclasses import dataclass
from typing import Any, Optional
from werkzeug.wrappers import Request as WerkzeugRequest
from werkzeug.wrappers import Response as WerkzeugResponse

@dataclass
class Request:
    path: str
    url: str
    ip: str
    
    args: dict[str, Any]
    input: dict[str, Any]
    
    query: dict[str, Any]
    files: dict[str, Any]
    
    headers: dict[str, str]
    cookies: dict[str, str]
    
    user: Optional[Any] = None

class Response(WerkzeugResponse):
    pass

class HTTPException(Exception):
    def __init__(self, status_code: int, message: Optional[str] = None):
        self.status_code = status_code
        self.message = message or f"HTTP {status_code}"
        super().__init__(self.message)

def make_lemur_request(request: WerkzeugRequest) -> Request:
    input_data = {}
    input_data.update(request.args.to_dict())
    
    if request.is_json:
        json_data = request.get_json(silent=True) or {}
        input_data.update(json_data)
    else:
        input_data.update(request.form.to_dict())
        
    return Request(
        path=request.path,
        url=request.url,
        ip=request.remote_addr or "127.0.0.1",
        
        args=request.args.to_dict(),
        input=input_data,
        query=request.args.to_dict(),
        files=request.files.to_dict(),
        
        headers=dict(request.headers),
        cookies=dict(request.cookies)
    )