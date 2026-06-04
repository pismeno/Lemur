import re
import html
from unittest import case

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
    
    if not words:
        return "", current_index

    match words[0]:
        case "foreach":
            return __handle_foreach(logic_content, words, tokens, current_index, var_table)
        case "endforeach":
            raise InvalidTemplateException("Unexpected 'endforeach' without an opening 'foreach' tag.")
        case "if":
            return __handle_if(logic_content, words, tokens, current_index, var_table)
        case "endif":
            raise InvalidTemplateException("Unexpected 'endif' without an opening 'if' tag.")
        case _:
            raise InvalidTemplateException(f"Unknown logic call: {logic_content}")


def __handle_foreach(logic_content: str, words: list, tokens: list, current_index: int, var_table: VarTable) -> tuple[str, int]:
    if not words[-1].startswith("@"):
        raise InvalidTemplateException(f"Invalid 'foreach' syntax: {logic_content}")
    
    iterable_var_name = words[-1][1:]
    iterable = var_table.get(iterable_var_name, [])
    
    inner_tokens, end_index = __get_inner_block(logic_content, tokens, current_index, "foreach", "endforeach")
    rendered_content = ""

    # Handle Lists
    if isinstance(iterable, list):
        if len(words) != 4 or not words[1].startswith("@") or words[2] != "in":
            raise InvalidTemplateException(f"Invalid 'foreach' syntax: {logic_content}")
            
        loop_var_name = words[1][1:]
        
        for item in iterable:
            var_table.enter_scope()
            var_table.define(loop_var_name, item) 
            rendered_content += __render_tokens(inner_tokens, var_table) 
            var_table.exit_scope()

    # Handle Dictionaries
    elif isinstance(iterable, dict):
        if len(words) != 5 or not words[1].startswith("@") or not words[2].startswith("@") or words[3] != "in":
            raise InvalidTemplateException(f"Invalid 'foreach' syntax: {logic_content}")
        
        key_var_name = words[1][1:]
        value_var_name = words[2][1:]
        
        for key, value in iterable.items():
            var_table.enter_scope()
            var_table.define(key_var_name, key) 
            var_table.define(value_var_name, value) 
            rendered_content += __render_tokens(inner_tokens, var_table) 
            var_table.exit_scope()
            
    else:
        raise InvalidTemplateException(f"Variable '{iterable_var_name}' is not iterable.")

    return rendered_content, end_index


def __handle_if(logic_content: str, words: list, tokens: list, current_index: int, var_table: VarTable) -> tuple[str, int]:
    if len(words) not in (2, 3):
        raise InvalidTemplateException(f"Invalid 'if' syntax: {logic_content}")
        
    is_negated = (len(words) == 3)
    
    if is_negated and words[1] != "not":
        raise InvalidTemplateException(f"Invalid 'if' syntax: {logic_content}")
        
    var_word = words[2] if is_negated else words[1]
    
    if not var_word.startswith("@"):
        raise InvalidTemplateException(f"Invalid 'if' syntax: {logic_content}")

    condition_var_name = var_word[1:]
    condition_value = var_table.get(condition_var_name, False)        

    if not isinstance(condition_value, bool):
        raise InvalidTemplateException(f"Variable '{condition_var_name}' is not a boolean.")
        
    if is_negated:
        condition_value = not condition_value
        
    inner_tokens, end_index = __get_inner_block(logic_content, tokens, current_index, "if", "endif")

    rendered_content = __render_tokens(inner_tokens, var_table) if condition_value else ""

    return rendered_content, end_index

def __get_inner_block(logic_content: str, tokens: list, start_index: int, open_tag: str, close_tag: str) -> tuple[list, int]:
    """Finds the matching closing tag and returns the inner tokens and the end index."""
    depth = 1
    end_index = start_index + 1
    
    while end_index < len(tokens):
        if tokens[end_index]["type"] == "LOGIC":
            inner_logic = tokens[end_index]["content"].strip().split()
            if not inner_logic:
                end_index += 1
                continue
                
            if inner_logic[0] == open_tag:
                depth += 1 
            elif inner_logic[0] == close_tag:
                depth -= 1
                if depth == 0:
                    break
        end_index += 1
        
    if depth != 0:
        raise InvalidTemplateException(f"Missing '{close_tag}' for statement starting with: {logic_content}")

    inner_tokens = tokens[start_index + 1 : end_index]
    return inner_tokens, end_index

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