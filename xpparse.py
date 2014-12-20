""" PLY parser for Siemens xprotocol XML-like format
"""
from __future__ import print_function, absolute_import

import re

# Known basic tag identifiers
basic_tag_ids = {'XProtocol': 'XPROTOCOL',
                 'Class': 'CLASS',
                 'Dll': 'DLL',
                 'Control': 'CONTROL',
                 'Param': 'PARAM',
                 'Pos': 'POS',
                 'Repr': 'REPR',
                 'Line': 'LINE',
                 'Context': 'CONTEXT',
                 'EVAStringTable': 'EVASTRINGTABLE',
                 'Name': 'NAME',
                 'ID': 'ID',
                 'Userversion': 'USERVERSION',
                }

# Known tag identifiers with defined types
typed_tag_ids = {'ParamBool': 'PARAMBOOL',
                 'ParamLong': 'PARAMLONG',
                 'ParamString': 'PARAMSTRING',
                 'ParamArray': 'PARAMARRAY',
                 'ParamMap': 'PARAMMAP',
                 'ParamChoice': 'PARAMCHOICE',
                 'ParamFunctor': 'PARAMFUNCTOR',
                 'ParamCardLayout': 'PARAMCARDLAYOUT',
                 'PipeService': 'PIPESERVICE',
                 'Connection': 'CONNECTION',
                 'Dependency': 'DEPENDENCY',
                 'Event': 'EVENT',
                 'Method': 'METHOD',
                }


tokens = [
    'TAG',
    'TYPED_TAG',
    'WHITESPACE',
    'INTEGER',
    'FLOAT',
    'MULTI_STRING',
    'TRUE',
    'FALSE',
] + list(basic_tag_ids.values()) + list(typed_tag_ids.values())

literals = '{}'

# Basic tag
def t_TAG(t):
    r'<(?P<tagname>[A-Za-z_][\w_]*)>'
    t.value = t.lexer.lexmatch.group('tagname')
    t.type = basic_tag_ids.get(t.value, 'TAG')
    return t


# Typed tag
def t_TYPED_TAG(t):
    r'<(?P<tagtype>[A-Za-z_][\w_]*)\."(?P<tagname>.*?)">'
    match = t.lexer.lexmatch
    t.value = match.group('tagname')
    t.type = typed_tag_ids.get(match.group('tagtype'))
    return t


# Whitespace
def t_WHITESPACE(t):
    r'\s+'
    t.lexer.lineno += t.value.count("\n")


# Floating literal
def t_FLOAT(t):
    r'((\d+)(\.\d+)(e(\+|-)?(\d+))? | (\d+)e(\+|-)?(\d+))([lL]|[fF])?'
    t.value = float(t.value)
    return t


# Integer literal
def t_INTEGER(t):
    r'[-]?[0-9]+'
    t.value = int(t.value)
    return t


def t_TRUE(t):
    r'"true"'
    t.value = True
    return t


def t_FALSE(t):
    r'"false"'
    t.value = False
    return t


def t_MULTI_STRING(t):
    r'"(?:[^"]|(?:"")|(?:\\x[0-9a-fA-F]+)|(?:\\.))*"'
    t.lexer.lineno += t.value.count("\n")
    t.value = t.value[1:-1]
    return t


def t_error(t):
    print("%d: Illegal character '%s'" % (t.lexer.lineno, t.value[0]))
    t.type = t.value[0]
    t.value = t.value[0]
    t.lexer.skip(1)
    return t


def p_xprotocols(p):
    """ xprotocols : xprotocols xprotocol
                   | xprotocol
    """
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


def p_xprotocol(p):
    """ xprotocol : XPROTOCOL '{' xp_hdr block_list cards depends '}'
    """
    p[0] = dict(type='xprotocol',
                blocks=p[4],
                cards=p[5],
                depends=p[6])
    p[0].update(p[3])


def p_xp_hdr(p):
    """ xp_hdr : xp_hdr xp_hdr_key
               | xp_hdr_key
    """
    if len(p) == 2:
        p[0] = dict([p[1]])
    else:
        p[0] = p[1]
        p[0].update(dict([p[2]]))


def p_xp_hdr_key(p):
    """ xp_hdr_key : NAME MULTI_STRING
                   | ID INTEGER
                   | USERVERSION FLOAT
    """
    p[0] = (p[1], p[2])


def p_xp_hdr_key_eva(p):
    """ xp_hdr_key : eva_string_table
    """
    p[0] = p[1]


def p_depends(p):
    """ depends : depends dependency
                | dependency
                |
    """
    if len(p) == 1:
        p[0] = []
    elif len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]


def p_cards(p):
    """ cards : cards param_card_layout
              | param_card_layout
              |
    """
    if len(p) == 1:
        p[0] = []
    elif len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]


def p_pipe_service(p):
    """ pipe_service : PIPESERVICE '{' class block_list '}'
    """
    p[0] = {'type': 'pipe_service',
            'name': p[1],
            'class': p[3],
            'value': p[4]}


def p_param_functor(p):
    """ param_functor : PARAMFUNCTOR '{' class block_list emc '}'
    """
    p[0] = {'type': 'param_functor',
            'name': p[1],
            'class': p[3],
            'value': p[4]}
    for param in p[5]:
        key = param['type']
        if key in p[0]:
            raise SyntaxError
        p[0][key] = param


def p_param_emc(p):
    """ emc : event method connection
            | event connection method
            | method event connection
            | method connection event
            | connection event method
            | connection method event
    """
    p[0] = p[1:4]


def p_method(p):
    """ method : METHOD '{' string_list '}'
    """
    p[0] = dict(type='method',
                name=p[1],
                args=p[3])


def p_connection(p):
    """ connection : CONNECTION '{' string_list '}'
    """
    p[0] = dict(type='connection',
                name=p[1],
                args=p[3])


def p_event(p):
    """ event : EVENT '{' string_list '}'
    """
    p[0] = dict(type='event',
                name=p[1],
                args=p[3])


def p_param_choice(p):
    """ param_choice : PARAMCHOICE '{' attr_list '}'
    """
    p[0] = dict(type='param_choice',
                name=p[1],
                attrs=p[3])


def p_param_map(p):
    """ param_map : PARAMMAP '{' block_list '}'
    """
    p[0] = dict(type='param_map',
                name=p[1],
                value=p[3])


def p_block_list(p):
    """ block_list : block_list block
                   | block
    """
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


def p_param_array(p):
    """ param_array : PARAMARRAY '{' attr_list '{' empty '}' '}'
                    | PARAMARRAY '{' attr_list curly_list '}'
    """
    p[0] = dict(type='param_array',
                name=p[1],
                attrs=p[3],
                value=p[4] if len(p) == 6 else [])


def p_block(p):
    """ block : param_bool
              | param_long
              | param_string
              | param_array
              | param_map
              | param_choice
              | param_functor
              | pipe_service
    """
    p[0] = p[1]


def p_param_string(p):
    """ param_string : PARAMSTRING '{' attr_list empty '}'
                     | PARAMSTRING '{' attr_list MULTI_STRING '}'
    """
    p[0] = dict(type='param_string',
                name=p[1],
                attrs=p[3],
                value=p[4])


def p_param_long(p):
    """ param_long : PARAMLONG '{' attr_list empty '}'
                   | PARAMLONG '{' attr_list INTEGER '}'
    """
    p[0] = dict(type='param_long',
                name=p[1],
                attrs=p[3],
                value=p[4])


def p_param_bool(p):
    """ param_bool : PARAMBOOL '{' attr_list empty '}'
                   | PARAMBOOL '{' attr_list TRUE '}'
                   | PARAMBOOL '{' attr_list FALSE '}'
    """
    p[0] = dict(type='param_bool',
                name=p[1],
                attrs=p[3],
                value=p[4])


def p_attr_list(p):
    """ attr_list : attr_list key_value
                  | key_value
                  |
    """
    if len(p) == 1: # empty
        p[0] = []
    elif len(p) == 2: # tagged params or key_value
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]


def p_key_value(p):
    """key_value : TAG curly_list
                 | TAG scalar
                 | TAG block
    """
    p[0] = (p[1], p[2])


def p_scalar(p):
    """scalar : FLOAT
              | INTEGER
              | FALSE
              | TRUE
              | MULTI_STRING
    """
    p[0] = p[1]


def p_dependency(p):
    """ dependency : DEPENDENCY '{' string_list empty empty '}'
                   | DEPENDENCY '{' string_list dll empty '}'
                   | DEPENDENCY '{' string_list dll context '}'
                   | DEPENDENCY '{' string_list empty context '}'
    """
    p[0] = dict(type='dependency',
                name=p[1],
                values=p[3],
                dll=p[4],
                context=p[5])


def p_curly_list(p):
    """ curly_list : '{' string_list '}'
                   | '{' integer_list '}'
                   | '{' float_list '}'
                   | '{' bool_list '}'
    """
    p[0] = p[2]


def p_scalar_lists(p):
    """ string_list : string_list MULTI_STRING
                    | MULTI_STRING
        integer_list : integer_list INTEGER
                    | INTEGER
        float_list : float_list FLOAT
                    | FLOAT
        bool_list : bool_list TRUE
                  | bool_list FALSE
                  | TRUE
                  | FALSE
    """
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


def p_param_card_layout(p):
    """ param_card_layout : PARAMCARDLAYOUT '{' repr controls lines '}'
    """
    p[0] = dict(type='param_card_layout',
                name=p[1],
                repr=p[3],
                controls=p[4],
                lines=p[5])


def p_controls(p):
    """ controls : controls control
                 | control
    """
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


def p_lines(p):
    """ lines : lines line
              | line
    """
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


def p_control(p):
    """ control : CONTROL '{' param pos repr '}'
                | CONTROL '{' param pos empty '}'
    """
    p[0] = dict(param=p[3],
                pos=p[4],
                repr=p[5])


def p_eva_string_table(p):
    """ eva_string_table : EVASTRINGTABLE '{' INTEGER int_strings '}'
    """
    p[0] = (p[1], (p[3], p[4]))


def p_int_strings(p):
    """ int_strings : int_strings int_string
                    | int_string
    """
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


def p_int_string(p):
    """ int_string : INTEGER MULTI_STRING """
    p[0] = (p[1], p[2])


def p_class(p):
    """class : CLASS MULTI_STRING
    """
    p[0] = p[2]


def p_context(p):
    """context : CONTEXT MULTI_STRING
    """
    p[0] = p[2]


def p_dll(p):
    """dll : DLL MULTI_STRING
    """
    p[0] = p[2]


def p_param(p):
    """param : PARAM MULTI_STRING
    """
    p[0] = p[2]


def p_repr(p):
    """repr : REPR MULTI_STRING
    """
    p[0] = p[2]


def p_pos(p):
    """pos : POS INTEGER INTEGER
    """
    p[0] = p[2:]


def p_line(p):
    """line : LINE '{' INTEGER INTEGER INTEGER INTEGER '}'
    """
    p[0] = p[3:7]


def p_empty(p):
    'empty :'


def p_error(p):
    if not p:
        print("Syntax error at EOF")
    print("Syntax error at '{0}', line {1}, col {2}".format(
        p.value, p.lineno, p.lexpos + 1))


def get_lexer():
    import ply.lex as lex
    return lex.lex()


def get_parser(start=None):
    import ply.yacc as yacc
    get_lexer()
    return yacc.yacc(start=start)


DBL_QUOTE_RE = re.compile(r'(?<!")""(?!")')

def strip_twin_quote(in_str):
    """ Replaces two double quotes together with one double quote

    Does so safely so that triple double quotes not touched.
    """
    return DBL_QUOTE_RE.sub('"', in_str)


ASCCONV_BLOCK = re.compile(
    r'(.*)?### ASCCONV BEGIN ###$(.*?)^### ASCCONV END ###',
    flags=re.M | re.S)

def split_ascconv(in_str):
    """ Split input string into xprotocol and ASCCONV
    """
    return ASCCONV_BLOCK.match(in_str).groups()
