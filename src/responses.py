import json
from werkzeug.wrappers import Response
from utils.assets import get_file_contents

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