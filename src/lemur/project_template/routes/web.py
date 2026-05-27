from lemur.routing import add_route
from lemur.responses import make_view_res

def gen_html(request):
    return make_view_res("test.html")

def gen_html_12(request):
    return make_view_res("2test.html")

add_route("/", "root", gen_html)
add_route("/test/", "test", gen_html_12)