from lemur.templating import make_view
from lemur.wrappers import HTTPException

__error_views = {}

def set_error_view(status_code: int, view_path: str) -> None:
    __error_views[status_code] = view_path

def make_error_view(e: Exception) -> str:
    status_code = e.status_code if isinstance(e, HTTPException) else 500
    view_path = __error_views.get(status_code)
    message = str(e) or "An unexpected error occurred."
    return make_view(view_path, {"message": message})