""" PLY parser for Siemens xprotocol XML-like format
"""
from __future__ import print_function, absolute_import

# Known tag identifiers
known_tag_ids = {'XProtocol': 'XPROTOCOL',
                 'ParamBool': 'PARAMBOOL',
                 'ParamLong': 'PARAMLONG',
                 'ParamString': 'PARAMSTRING',
                 'ParamArray': 'PARAMARRAY',
                 'ParamMap': 'PARAMMAP',
                 'ParamChoice': 'PARAMCHOICE',
                 'ParamFunctor': 'PARAMFUNCTOR',
                 'ParamCardLayout': 'PARAMCARDLAYOUT',
                 'PipeService': 'PIPESERVICE',
                 'Class': 'CLASS',
                 'Event': 'EVENT',
                 'Method': 'METHOD',
                 'Connection': 'CONNECTION',
                 'Dependency': 'DEPENDENCY'}

tokens = [
    'ID',
    'WHITESPACE',
    'INTEGER',
    'FLOAT',
    'MULTI_STRING',
    'TRUE',
    'FALSE',
] + list(known_tag_ids)

literals = '<>.{}'

# Identifier
def t_ID(t):
    r'[A-Za-z_][\w_]*'
    t.type = known_tag_ids.get(t.value, 'ID')
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
    r'(((((0x)|(0X))[0-9a-fA-F]+)|(\d+))([uU]|[lL]|[uU][lL]|[lL][uU])?)'
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
    t.type = t.value[0]
    t.value = t.value[0]
    t.lexer.skip(1)
    return t


def p_compact_keys_values(p):
    """keys_values : keys_values keys_values
    """
    p[0] = p[1] + p[2]


def p_key_value_keys_values(p):
    """keys_values : key_value
    """
    p[0] = [p[1]]


def p_key_list(p):
    """key_value : id_tag list
    """
    p[0] = (p[1], p[2])


def p_key_scalar(p):
    """key_value : id_tag scalar
    """
    p[0] = (p[1], p[2])


def p_id_tag(p):
    """id_tag : '<' ID '>'
    """
    p[0] = p[2]


def p_list_list_scalar(p):
    """list : list scalar
    """
    p[0] = p[1][:]
    p[0].append(p[2])


def p_list_two_scalars(p):
    """list : scalar scalar
    """
    p[0] = [p[1], p[2]]


def p_scalar(p):
    """scalar : FLOAT
              | INTEGER
              | FALSE
              | TRUE
              | MULTI_STRING
    """
    p[0] = p[1]


def p_error(p):
    print("Syntax error in input!")


def get_lexer():
    import ply.lex as lex
    return lex.lex()


def get_parser(start=None):
    import ply.yacc as yacc
    get_lexer()
    return yacc.yacc(start=start)
