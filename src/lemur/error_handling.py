from lemur.templating import make_view

__error_views = {}

def set_error_view(status_code: int, view_path: str) -> None:
    __error_views[status_code] = view_path

def make_error_view(status_code: int) -> str:
    return make_view(__error_views.get(status_code))