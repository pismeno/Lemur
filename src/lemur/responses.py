import json
import requests
import mimetypes
from pathlib import Path
from werkzeug.wrappers import Response
from lemur.templating import make_view
from lemur.error_handling import make_error_view
from lemur.utils.assets import private_path
from lemur.utils.assets import get_private_file_contents
from lemur.utils.assets import get_public_file_contents

def make_json_res(data: dict, status: int = 200) -> Response:
    json_string = json.dumps(data)

    return Response(
        response=json_string,
        status=status,
        mimetype="application/json"
    )

def make_file_content_res(file_path: str, mimetype: str = None, private: bool = False) -> Response:
    if not mimetype:
        mimetype, _ = mimetypes.guess_type(file_path)
        if not mimetype:
            mimetype = 'application/octet-stream'
    
    try:
        if private:
            file_content = get_private_file_contents(file_path)
        else:
            file_content = get_public_file_contents(file_path)
    except FileNotFoundError:
        return make_error_view_res(404)
    
    return Response(
        response=file_content,
        status=200,
        mimetype=mimetype
    )

def make_view_res(view_path: str, context: dict = None, status: int = 200) -> Response:
    view_content = make_view(view_path, context)

    return Response(
        response=view_content,
        status=status,
        mimetype="text/html"
    )

def make_error_view_res(status: int) -> Response:
    error_content = make_error_view(status)

    return Response(
        response=error_content,
        status=status,
        mimetype="text/html"
    )

def make_spa_app_res(app_path: str) -> Response:
    path_obj = Path(app_path)
    target_path = private_path / path_obj

    if target_path.is_file():
        mimetype, _ = mimetypes.guess_type(target_path)
        
        if not mimetype:
            mimetype = 'application/octet-stream' 
            
        with open(target_path, 'rb') as file:
            return Response(file.read(), status=200, mimetype=mimetype)

    if target_path.suffix in ['.js', '.css', '.ico', '.json', '.map']:
        return Response(f"Asset missing at physical path: {target_path}", status=404, mimetype="text/plain")

    app_name = path_obj.parts[0] if path_obj.parts else ''
    index_path = private_path / app_name / 'index.html'
    
    if index_path.is_file():
        with open(index_path, 'rb') as f:
            return Response(f.read(), status=200, mimetype='text/html')

    return Response(f"Not found: {target_path}", status=404, mimetype="text/plain")

def make_proxy_res(target_url: str, method: str = "GET", data: bytes = None) -> Response:
    try:
        external_response = requests.request(
            method=method,
            url=target_url,
            data=data,
            stream=True
        )

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = [
            (k, v) for k, v in external_response.headers.items()
            if k.lower() not in excluded_headers
        ]

        return Response(
            response=external_response.content,
            status=external_response.status_code,
            headers=response_headers,
            mimetype=external_response.headers.get('content-type')
        )

    except requests.RequestException as e:
        return Response(
            response=f"Proxy Error: {e}",
            status=502,
            mimetype="text/plain"
        )