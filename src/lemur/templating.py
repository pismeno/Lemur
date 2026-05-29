import re
import html
from lemur.utils.assets import PRIVATE_PATH, get_private_file_contents, get_safe_path

__regex_pattern = r'(?P<VARIABLE>\{\{.*?\}\})|(?P<UNESCAPED_VARIABLE>\{!.*?!\})|(?P<SUBTEMPLATE>\<\<.*?\>\>)'

__templates_cache = {}
__templates_timestamps = {}

def make_view(view_path: str, context: dict = None) -> str:
    if context is None:
        context = {}

    actual_view_path = view_path if view_path.endswith('.tail') else view_path + '.tail'

    safe_view_path = get_safe_path(PRIVATE_PATH, actual_view_path)
    modification_time = safe_view_path.stat().st_mtime

    template_tokens = __templates_cache.get(actual_view_path)
    
    if not template_tokens or __templates_timestamps.get(actual_view_path) != modification_time:
        template_content = get_private_file_contents(actual_view_path)
        template_tokens = __tokenize_template(template_content)
        __templates_cache[actual_view_path] = template_tokens

    rendered_content = ""

    for token in template_tokens:
        if token["type"] == "TEXT":
            rendered_content += token["content"]
        elif token["type"] == "VARIABLE":
            variable_name = token["content"].strip()
            variable_value = context.get(variable_name, "")
            rendered_content += html.escape(str(variable_value))
        elif token["type"] == "UNESCAPED_VARIABLE":
            variable_name = token["content"].strip()
            variable_value = context.get(variable_name, "")
            rendered_content += str(variable_value)
        elif token["type"] == "SUBTEMPLATE":
            rendered_content += make_view(token["content"].strip(), context)
            pass

    return rendered_content

def __tokenize_template(template_content: str) -> list:
    tokens = []
    last_end = 0

    for match in re.finditer(__regex_pattern, template_content):
        start, end = match.span()
        
        if start > last_end:
            tokens.append({
                "type": "TEXT",
                "content": template_content[last_end:start]
            })
            
        tag_type = match.lastgroup
        raw_tag = match.group()
        
        inner_content = raw_tag[2:-2] # strip the brackets to get the inner content (2 characters on each side)
        
        tokens.append({
            "type": tag_type,
            "content": inner_content,
        })
        
        last_end = end

    if last_end < len(template_content):
        tokens.append({
            "type": "TEXT",
            "content": template_content[last_end:]
        })

    return tokens