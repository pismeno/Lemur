from routing import add_route

def gen_html(request):
    return "<h1>Test success</h1>"

add_route("/", "root", gen_html)