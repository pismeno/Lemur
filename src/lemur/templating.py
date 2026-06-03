import re
import html

from lemur.utils.assets import LEMUR_PRIVATE_PATH, PRIVATE_PATH, get_private_file_contents, get_safe_path
from lemur.utils.collections import VarTable
from lemur.exceptions import InvalidTemplateException

__regex_pattern = (
    r'(?P<VARIABLE>\{\{.*?\}\})|'
    r'(?P<UNESCAPED_VARIABLE>\{!.*?!\})|'
    r'(?P<SUBTEMPLATE>\<\<.*?\>\>)|'
    r'(?P<LOGIC>\{#.*?#\})'
)

__templates_cache = {}
__templates_timestamps = {}

def make_view(view_path: str, context: dict = None) -> str:
    var_table = VarTable(context)

    actual_view_path = view_path if view_path.endswith('.tail') else view_path + '.tail'

    if actual_view_path.startswith("/lemur"):
        safe_view_path = get_safe_path(LEMUR_PRIVATE_PATH, actual_view_path.removeprefix("/lemur"))
    else:
        safe_view_path = get_safe_path(PRIVATE_PATH, actual_view_path)
        
    modification_time = safe_view_path.stat().st_mtime

    template_tokens = __templates_cache.get(actual_view_path)
    
    if not template_tokens or __templates_timestamps.get(actual_view_path) != modification_time:
        template_content = get_private_file_contents(actual_view_path)
        template_tokens = __tokenize_template(template_content)
        __templates_cache[actual_view_path] = template_tokens
        __templates_timestamps[actual_view_path] = modification_time

    return __render_tokens(template_tokens, var_table)

def __render_tokens(tokens: list, var_table: VarTable) -> str:
    rendered_content = ""
    i = 0
    
    while i < len(tokens):
        token = tokens[i]
        
        if token["type"] == "TEXT":
            rendered_content += token["content"]
            
        elif token["type"] == "VARIABLE":
            variable_name = token["content"].strip()
            variable_value = var_table.get(variable_name, "")
            rendered_content += html.escape(str(variable_value))
            
        elif token["type"] == "UNESCAPED_VARIABLE":
            variable_name = token["content"].strip()
            variable_value = var_table.get(variable_name, "")
            rendered_content += str(variable_value)
            
        elif token["type"] == "SUBTEMPLATE":
            rendered_content += make_view(token["content"].strip(), var_table.to_dict())
            
        elif token["type"] == "LOGIC":
            logic_output, i = __handle_logic_token(tokens, i, var_table)
            rendered_content += logic_output

        i += 1

    return rendered_content

def __handle_logic_token(tokens: list, current_index: int, var_table: VarTable) -> tuple[str, int]:
    token = tokens[current_index]
    logic_content = token["content"].strip()
    words = logic_content.split()
    
    if words[0] == "foreach":
        if len(words) != 4 or not words[1].startswith("@") or words[2] != "in" or not words[3].startswith("@"):
            raise InvalidTemplateException(f"Invalid 'foreach' syntax: {logic_content}")
        
        loop_var_name = words[1][1:]
        iterable_var_name = words[3][1:]
        iterable = var_table.get(iterable_var_name, [])
        
        if not isinstance(iterable, list):
            raise InvalidTemplateException(f"Variable '{iterable_var_name}' is not a list.")

        depth = 1
        end_index = current_index + 1
        while end_index < len(tokens):
            if tokens[end_index]["type"] == "LOGIC":
                inner_logic = tokens[end_index]["content"].strip().split()
                if inner_logic[0] == "foreach":
                    depth += 1 
                elif inner_logic[0] == "endforeach":
                    depth -= 1
                    if depth == 0:
                        break
            end_index += 1
        
        if depth != 0:
            raise InvalidTemplateException(f"Missing 'endforeach' for loop starting with: {logic_content}")

        inner_tokens = tokens[current_index + 1 : end_index]
        rendered_content = ""

        for item in iterable:
            var_table.enter_scope()
            var_table.define(loop_var_name, item) 
            rendered_content += __render_tokens(inner_tokens, var_table) 
            var_table.exit_scope()

        return rendered_content, end_index

    elif words[0] == "endforeach":
        raise InvalidTemplateException("Unexpected 'endforeach' without an opening 'foreach' tag.")
    
    if words[0] == "if":
        if len(words) > 3 or len(words) < 2:
            raise InvalidTemplateException(f"Invalid 'if' syntax: {logic_content}")
        
        if len(words) == 3:
            if not words[1] == "not":
                raise InvalidTemplateException(f"Invalid 'if' syntax: {logic_content}")
            if not words[2].startswith("@"):
                raise InvalidTemplateException(f"Invalid 'if' syntax: {logic_content}")
            
            condition_var_name = words[2][1:]
            condition_value = var_table.get(condition_var_name, False)
            
        if len(words) == 2:
            if not words[1].startswith("@"):
                raise InvalidTemplateException(f"Invalid 'if' syntax: {logic_content}")

            condition_var_name = words[1][1:]
            condition_value = var_table.get(condition_var_name, False)        

        if condition_value not in [True, False]:
            raise InvalidTemplateException(f"Variable '{condition_var_name}' is not a boolean.")
        
        if len(words) == 3:
            condition_value = not condition_value
        
        depth = 1
        end_index = current_index + 1
        while end_index < len(tokens):
            if tokens[end_index]["type"] == "LOGIC":
                inner_logic = tokens[end_index]["content"].strip().split()
                if inner_logic[0] == "if":
                    depth += 1 
                elif inner_logic[0] == "endif":
                    depth -= 1
                    if depth == 0:
                        break
            end_index += 1
        
        if depth != 0:
            raise InvalidTemplateException(f"Missing 'endif' for 'if' statement starting with: {logic_content}")

        inner_tokens = tokens[current_index + 1 : end_index]
        rendered_content = ""

        if condition_value:
            rendered_content = __render_tokens(inner_tokens, var_table)

        return rendered_content, end_index
        
    else:
        raise InvalidTemplateException(f"Unknown logic call: {logic_content}")

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