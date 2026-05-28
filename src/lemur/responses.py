import json
import requests
from werkzeug.wrappers import Response
from lemur.utils.assets import get_file_contents

def make_json_res(data: dict, status: int = 200) -> Response:
    json_string = json.dumps(data)

    return Response(
        response=json_string,
        status=status,
        mimetype="application/json"
    )

def make_view_res(view_path: str, status: int = 200) -> Response:
    view_content = get_file_contents(view_path)

    return Response(
        response=view_content,
        status=status,
        mimetype="text/html"
    )

import requests
from werkzeug.wrappers import Response

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