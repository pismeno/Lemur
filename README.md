# About
Lemur is a backend web framework, featuring Routing, Request Handling, HTML Templating, Error handling and a simple CLI.

# Project status
Currently abandoned, but is ready to use, and completely possible to make a web with.

# How to create a Lemur project?

Install lemur python module:
`pip install lemur11`

Make sure Lemur is installed:
`lemur --help`

Initialize a project:
`lemur init project_name`
cd into your project:
`cd project_name`

# Features / How to use?
## Routing
To make a new routing file run:
`lemur make router file_name`

All scripts inside routes/ are automatically executed, therefore you don't have to register this router anywhere.

To mount a new route use:
```python
from lemur.routing import add_route

def add_route(
    url: str,
    name: str, 
    function: Callable[[LemurRequest], LemurResponse], 
    methods: list[str] = None
) -> None
```
You can also mount a Single Page Application using:
```python
from lemur.routing import mount_spa

def mount_spa(
        url_prefix: str, 
        name: str, 
        app_directory: str
        ) -> None
```

## Error handling
These methods can be used to customize what users see when you encounter an error:
```python
from lemur.error_handling import set_default_error_view, set_error_view

def set_default_error_view(view_path: str) -> None
def set_error_view(status_code: int, view_path: str) -> None
```

## Templates (tails)

The templating engine lets you write logic directly into your HTML.
### Variables
Inject dynamic data using double curly braces. 
```html
<a href="{{ file_link }}">{{ variable_name }}</a>
```
### Subtemplates
Include reusable partial views.
```html
<nav><< components/navbar >></nav>
```
### Conditionals
Control visibility with if and if not blocks. Prefix boolean variables with @
```html
{# if @is_logged_in #}
  <button>Logout</button>
{# endif #}

{# if not @has_errors #}
  <span>Success!</span>
{# endif #}
```
### Loops
Iterate over lists or dictionaries. Map items to local variables using the variable @ prefix.
```html
<!-- List Iteration -->
<ul>
  {# foreach @user in @users #}
    <li>{{ user }}</li>
  {# endforeach #}
</ul>

<!-- Dictionary Iteration -->
<dl>
  {# foreach @key @val in @settings #}
    <dt>{{ key }}</dt>
    <dd>{{ val }}</dd>
  {# endforeach #}
</dl>
```
## Responses
You can respond to a request in the following ways:

json response:
```python
from lemur.responses import make_json_res

def make_json_res(
    data: dict, 
    status: int = 200
    ) -> Response
```

response with a file content:
```python
from lemur.responses import make_file_content_res

def make_file_content_res(
    file_path: str, 
    mimetype: str = None, 
    private: bool = False # Whether to search for the file in private/ rather than public/
    ) -> Response
```

view response from a template:
```python
from lemur.responses import make_view_res

def make_view_res(
    view_path: str, 
    context: dict = None, # the data for the templating engine to parse into the template
    status: int = 200
    ) -> Response
```

view reponse from a template associated with the error:
```python
from lemur.responses import make_error_view_res

def make_error_view_res(e: Exception) -> Response:
```

# Used libraries / modules
- werkzeug
- requests
- typer

# Architecture
This framework is strictly procedural.

# About the repository
this repository uses the conventional commits format: https://www.conventionalcommits.org/en/v1.0.0/
main branch is the latest stable release.
dev branch is the latest working development version.
feat/ branches are implementations of new features.
fix/ branches are bugfixes.
docs/ branches are documentation.