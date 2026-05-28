import re
import html
from lemur.utils.assets import get_file_contents

__templates_cache = {}

def make_view(view_path: str, context: dict = None) -> str:
    if context is None:
        context = {}

    template_tokens = __templates_cache.get(view_path)
    
    if not template_tokens:
        template_content = get_file_contents(view_path)
        template_tokens = __tokenize_template(template_content)
        __templates_cache[view_path] = template_tokens

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
            pass

    return rendered_content

def __tokenize_template(template_content: str) -> list:
    regex_pattern = r'(?P<VARIABLE>\{\{.*?\}\})|(?P<UNESCAPED_VARIABLE>\{!.*?!\})'

    tokens = []
    last_end = 0

    for match in re.finditer(regex_pattern, template_content):
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