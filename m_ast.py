#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2019, Florian Schanda                         ##
##                                                                          ##
##  This file is part of MISS_HIT.                                          ##
##                                                                          ##
##  MATLAB Independent, Small & Safe, High Integrity Tools (MISS_HIT) is    ##
##  free software: you can redistribute it and/or modify it under the       ##
##  terms of the GNU General Public License as published by the Free        ##
##  Software Foundation, either version 3 of the License, or (at your       ##
##  option) any later version.                                              ##
##                                                                          ##
##  MISS_HIT is distributed in the hope that it will be useful,             ##
##  but WITHOUT ANY WARRANTY; without even the implied warranty of          ##
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           ##
##  GNU General Public License for more details.                            ##
##                                                                          ##
##  You should have received a copy of the GNU General Public License       ##
##  along with MISS_HIT. If not, see <http://www.gnu.org/licenses/>.        ##
##                                                                          ##
##############################################################################

from m_lexer import MATLAB_Token
from errors import ICE

NODE_UID = [0]


class Node:
    def __init__(self):
        NODE_UID[0] += 1
        self.uid = NODE_UID[0]


class Expression(Node):
    pass


class Script_File(Node):
    def __init__(self, name, n_statements, l_functions):
        super().__init__()
        assert isinstance(name, str)
        assert isinstance(n_statements, Sequence_Of_Statements)
        assert isinstance(l_functions, list)
        for n_function in l_functions:
            assert isinstance(n_function, Function_Definition)

        self.name         = name
        # Not a node since it comes from the filename

        self.n_statements = n_statements
        self.l_functions  = l_functions


class Sequence_Of_Statements(Node):
    def __init__(self, l_statements):
        super().__init__()
        assert isinstance(l_statements, list)
        for statement in l_statements:
            assert isinstance(statement, Statement)

        self.l_statements = l_statements


class Statement(Node):
    pass


class Function_Definition(Node):
    def __init__(self, t_fun, n_name, l_inputs, l_outputs, n_body):
        super().__init__()
        assert isinstance(t_fun, MATLAB_Token)
        assert t_fun.kind == "KEYWORD" and t_fun.value() == "function"
        assert isinstance(n_name, Name)
        assert isinstance(l_inputs, list)
        for n in l_inputs:
            assert isinstance(n, Identifier), \
                str(n) + " is %s and not an Identifier" % n.__class__.__name__
        for n in l_outputs:
            assert isinstance(n, Identifier)
        assert isinstance(l_outputs, list)
        assert isinstance(n_body, Sequence_Of_Statements)

        self.t_fun     = t_fun
        self.n_name    = n_name
        self.l_inputs  = l_inputs
        self.l_outputs = l_outputs
        self.n_body    = n_body


class Class_Attribute(Node):
    """ AST for items of the various attribute lists inside classdefs

    For example (Access = protected)
    """
    def __init__(self, n_name, n_value=None):
        super().__init__()
        assert isinstance(n_name, Identifier)
        assert n_value is None or isinstance(n_value, Expression)

        self.n_name = n_name
        self.n_value = n_value


class Class_Block(Node):
    """ AST for properties, methods, events and enumeration blocks """
    def __init__(self, t_kw, l_attr):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value() in ("properties",
                                                           "methods",
                                                           "events",
                                                           "enumeration")
        assert isinstance(l_attr, list)
        for n_attr in l_attr:
            assert isinstance(n_attr, Class_Attribute)

        self.t_kw = t_kw
        self.l_attr = l_attr
        self.l_items = []

    def kind(self):
        return self.t_kw.value()

    def add_property(self, n_prop):
        assert isinstance(n_prop, Class_Property)
        assert self.kind() == "properties"
        self.l_items.append(n_prop)

    def add_method(self, n_method):
        assert isinstance(n_method, Function_Definition)
        assert self.kind() == "methods"
        self.l_items.append(n_method)

    def add_enumeration(self, n_enum):
        assert isinstance(n_enum, Class_Enumeration)
        assert self.kind() == "enumeration"
        self.l_items.append(n_enum)

    def add_event(self, n_event):
        assert isinstance(n_event, Identifier)
        assert self.kind() == "events"
        self.l_items.append(n_event)


class Class_Property(Node):
    """ AST for a class property (inside a properties block """
    def __init__(self, n_name,
                 l_dim_constraint, n_class_constraint, l_fun_constraint,
                 n_default_value):
        super().__init__()
        assert isinstance(n_name, Identifier)
        assert isinstance(l_dim_constraint, list)
        assert len(l_dim_constraint) != 1
        for n_dim_constraint in l_dim_constraint:
            assert isinstance(n_dim_constraint, MATLAB_Token)
            assert n_dim_constraint.kind in ("NUMBER", "COLON")
        assert n_class_constraint is None or isinstance(n_class_constraint,
                                                        Name)
        assert isinstance(l_fun_constraint, list)
        for n_fun_constraint in l_fun_constraint:
            assert isinstance(n_fun_constraint, Name)
        assert n_default_value is None or isinstance(n_default_value,
                                                     Expression)

        self.n_name             = n_name
        self.l_dim_constraint   = l_dim_constraint
        self.n_class_constraint = n_class_constraint
        self.l_fun_constraint   = l_fun_constraint
        self.n_default_value    = n_default_value


class Class_Enumeration(Node):
    """ AST for enumeration literal/constructors inside classdefs """
    def __init__(self, n_name, l_args):
        super().__init__()
        assert isinstance(n_name, Identifier)
        assert isinstance(l_args, list)
        for n_arg in l_args:
            assert isinstance(n_arg, Expression)

        self.n_name = n_name
        self.l_args = l_args


class Class_Definition(Node):
    def __init__(self, t_classdef, n_name, l_attr, l_super):
        super().__init__()
        assert isinstance(t_classdef, MATLAB_Token)
        assert t_classdef.kind == "KEYWORD" and \
            t_classdef.value() == "classdef"
        assert isinstance(n_name, Name)
        assert isinstance(l_attr, list)
        for n_attr in l_attr:
            assert isinstance(n_attr, Class_Attribute)
        assert isinstance(l_super, list)
        for n_super in l_super:
            assert isinstance(n_super, Name)

        self.t_classdef = t_classdef
        self.n_name = n_name
        self.l_super = l_super
        self.l_attr = l_attr

        self.l_properties = []
        self.l_events = []
        self.l_enumerations = []
        self.l_methods = []

    def add_block(self, n_block):
        assert isinstance(n_block, Class_Block)

        if n_block.kind() == "properties":
            self.l_properties.append(n_block)
        elif n_block.kind() == "methods":
            self.l_methods.append(n_block)
        elif n_block.kind() == "events":
            self.l_events.append(n_block)
        elif n_block.kind() == "enumeration":
            self.l_enumerations.append(n_block)
        else:
            raise ICE("unexpected block kind %s" % n_block.kind())


class Name(Expression):
    pass


class Reference(Name):
    def __init__(self, n_ident, arglist):
        super().__init__()
        assert isinstance(n_ident, Name)
        assert isinstance(arglist, list)
        for arg in arglist:
            assert isinstance(arg, Expression)

        self.n_ident = n_ident
        self.arglist = arglist

    def __str__(self):
        if self.arglist:
            return "%s(%s)" % (self.n_ident, ", ".join(map(str, self.arglist)))
        else:
            return str(self.n_ident)


class Cell_Reference(Name):
    def __init__(self, n_ident, arglist):
        super().__init__()
        assert isinstance(n_ident, Name)
        assert isinstance(arglist, list)
        for arg in arglist:
            assert isinstance(arg, Expression)

        self.n_ident = n_ident
        self.arglist = arglist

    def __str__(self):
        if self.arglist:
            return "%s{%s}" % (self.n_ident, ", ".join(map(str, self.arglist)))
        else:
            return str(self.n_ident)


class Identifier(Name):
    def __init__(self, t_ident):
        super().__init__()
        assert isinstance(t_ident, MATLAB_Token)
        assert t_ident.kind == "IDENTIFIER" or \
            (t_ident.kind == "OPERATOR" and t_ident.value() == "~") or \
            (t_ident.kind == "KEYWORD" and t_ident.value() == "end") or \
            t_ident.kind == "BANG"

        self.t_ident = t_ident

    def __str__(self):
        if self.t_ident.kind == "BANG":
            return "system"
        else:
            return self.t_ident.value()


class Selection(Name):
    def __init__(self, t_selection, n_prefix, n_field):
        super().__init__()
        assert isinstance(t_selection, MATLAB_Token)
        assert t_selection.kind == "SELECTION"
        assert isinstance(n_prefix, Name)
        assert isinstance(n_field, Identifier)

        self.t_selection = t_selection
        self.n_prefix    = n_prefix
        self.n_field     = n_field

    def __str__(self):
        return "%s.%s" % (self.n_prefix, self.n_field)


class Dynamic_Selection(Name):
    def __init__(self, t_selection, n_prefix, n_field):
        super().__init__()
        assert isinstance(t_selection, MATLAB_Token)
        assert t_selection.kind == "SELECTION"
        assert isinstance(n_prefix, Name)
        assert isinstance(n_field, Expression)

        self.t_selection = t_selection
        self.n_prefix    = n_prefix
        self.n_field     = n_field

    def __str__(self):
        return "%s.(%s)" % (self.n_prefix, self.n_field)


class Superclass_Reference(Name):
    def __init__(self, t_at, n_prefix, n_reference):
        super().__init__()
        assert isinstance(t_at, MATLAB_Token)
        assert t_at.kind == "AT"
        assert isinstance(n_prefix, Identifier)
        assert isinstance(n_reference, Name)

        self.t_at = t_at
        self.n_prefix = n_prefix
        self.n_reference = n_reference

    def __str__(self):
        return "%s@%s" % (self.n_prefix, self.n_reference)


class Reshape(Expression):
    def __init__(self, t_colon):
        super().__init__()
        assert isinstance(t_colon, MATLAB_Token)
        assert t_colon.kind == "COLON"

        self.t_colon = t_colon

    def __str__(self):
        return ":"


class Range_Expression(Expression):
    def __init__(self, n_first, n_last, n_stride=None):
        super().__init__()
        assert isinstance(n_first, Expression)
        assert isinstance(n_last, Expression)
        assert n_stride is None or isinstance(n_stride, Expression)

        self.n_first = n_first
        self.n_last = n_last
        if n_stride is None:
            # TODO, replace with a stride of 1 of the appropriate type
            self.n_stride = None
        else:
            self.n_stride = n_stride

    def __str__(self):
        if self.n_stride:
            return "%s:%s:%s" % (self.n_first, self.n_stride, self.n_last)
        else:
            return "%s:%s" % (self.n_first, self.n_last)


class Matrix_Expression(Expression):
    def __init__(self, t_open, t_close, items):
        super().__init__()
        assert isinstance(t_open, MATLAB_Token)
        assert isinstance(t_close, MATLAB_Token)
        assert isinstance(items, list)
        for row in items:
            assert isinstance(row, list)
            for item in row:
                assert isinstance(item, Expression)

        self.t_open  = t_open
        self.t_close = t_close
        self.items   = items

    def __str__(self):
        rows = []
        for row in self.items:
            rows.append(", ".join(str(item) for item in row))
        return "[" + "; ".join(rows) + "]"


class Cell_Expression(Expression):
    def __init__(self, t_open, t_close, items):
        super().__init__()
        assert isinstance(t_open, MATLAB_Token)
        assert isinstance(t_close, MATLAB_Token)
        assert isinstance(items, list)
        for row in items:
            assert isinstance(row, list)
            for item in row:
                assert isinstance(item, Expression)

        self.t_open  = t_open
        self.t_close = t_close
        self.items   = items

    def __str__(self):
        rows = []
        for row in self.items:
            rows.append(", ".join(str(item) for item in row))
        return "{" + "; ".join(rows) + "}"


class Function_Call(Expression):
    def __init__(self, n_name, l_args, variant="normal"):
        super().__init__()
        assert isinstance(n_name, Name)
        assert isinstance(l_args, list)
        for n_arg in l_args:
            assert isinstance(n_arg, Expression)
            if variant in ("command", "escape"):
                assert isinstance(n_arg, Char_Array_Literal)
        assert variant in ("normal", "command", "escape")
        if variant == "escape":
            assert str(n_name) == "system"
            assert len(l_args) == 1

        self.variant = variant
        self.n_name = n_name
        self.l_args = l_args

    def __str__(self):
        if self.variant == "normal":
            return "%s(%s)" % (self.n_name,
                               ", ".join(map(str, self.l_args)))
        elif self.variant == "command":
            return "%s %s" % (self.n_name,
                              " ".join(map(str, self.l_args)))
        else:
            return "!%s" % str(self.l_args[0])


class Simple_For_Statement(Statement):
    def __init__(self, t_for, n_ident, n_range, n_body):
        super().__init__()
        assert isinstance(t_for, MATLAB_Token)
        assert t_for.kind == "KEYWORD" and t_for.value() == "for"
        assert isinstance(n_ident, Identifier)
        assert isinstance(n_range, Range_Expression)
        assert isinstance(n_body, Sequence_Of_Statements)

        self.t_for   = t_for
        self.n_ident = n_ident
        self.n_range = n_range
        self.n_body  = n_body


class General_For_Statement(Statement):
    def __init__(self, t_for, n_ident, n_expr, n_body):
        super().__init__()
        assert isinstance(t_for, MATLAB_Token)
        assert t_for.kind == "KEYWORD" and t_for.value() == "for"
        assert isinstance(n_ident, Identifier)
        assert isinstance(n_expr, Expression)
        assert isinstance(n_body, Sequence_Of_Statements)

        self.t_for   = t_for
        self.n_ident = n_ident
        self.n_expr = n_expr
        self.n_body  = n_body


class While_Statement(Statement):
    def __init__(self, t_while, n_guard, n_body):
        super().__init__()
        assert isinstance(t_while, MATLAB_Token)
        assert t_while.kind == "KEYWORD" and t_while.value() == "while"
        assert isinstance(n_guard, Expression)
        assert isinstance(n_body, Sequence_Of_Statements)

        self.t_while = t_while
        self.n_guard = n_guard
        self.n_body  = n_body


class If_Statement(Statement):
    def __init__(self, actions):
        super().__init__()
        assert isinstance(actions, list)
        assert len(actions) >= 1
        for action in actions:
            assert isinstance(action, tuple) and len(action) == 3
            t_kw, n_expr, n_body = action
            assert isinstance(t_kw, MATLAB_Token)
            assert t_kw.kind == "KEYWORD" and t_kw.value() in ("if",
                                                               "elseif",
                                                               "else")
            assert n_expr is None or isinstance(n_expr, Expression)
            assert isinstance(n_body, Sequence_Of_Statements)

        self.actions = actions
        self.has_else = actions[-1][0].value() == "else"


class Switch_Statement(Statement):
    def __init__(self, t_kw, n_switch_expr, l_options):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value() == "switch"
        assert isinstance(n_switch_expr, Expression)
        assert isinstance(l_options, list)
        assert len(l_options) >= 1
        for option in l_options:
            assert isinstance(option, tuple) and len(option) == 3
            t_kw, n_expr, n_body = option
            assert isinstance(t_kw, MATLAB_Token)
            assert t_kw.kind == "KEYWORD" and t_kw.value() in ("case",
                                                               "otherwise")
            assert n_expr is None or isinstance(n_expr, Expression)
            assert isinstance(n_body, Sequence_Of_Statements)

        self.t_kw = t_kw
        self.n_expr = n_switch_expr
        self.l_options = l_options
        self.has_otherwise = l_options[-1][0].value() == "otherwise"


class Simple_Assignment_Statement(Statement):
    def __init__(self, t_eq, n_lhs, n_rhs):
        super().__init__()
        assert isinstance(t_eq, MATLAB_Token)
        assert t_eq.kind == "ASSIGNMENT"
        assert isinstance(n_lhs, Name)
        assert isinstance(n_rhs, Expression)

        self.t_eq  = t_eq
        self.n_lhs = n_lhs
        self.n_rhs = n_rhs


class Compound_Assignment_Statement(Statement):
    def __init__(self, t_eq, l_lhs, n_rhs):
        super().__init__()
        assert isinstance(t_eq, MATLAB_Token)
        assert t_eq.kind == "ASSIGNMENT"
        assert isinstance(l_lhs, list)
        assert len(l_lhs) >= 2
        for n_lhs in l_lhs:
            assert isinstance(n_lhs, Name)
        assert isinstance(n_rhs, Expression)

        self.t_eq  = t_eq
        self.l_lhs = l_lhs
        self.n_rhs = n_rhs


class Naked_Expression_Statement(Statement):
    def __init__(self, n_expr):
        super().__init__()
        assert isinstance(n_expr, Expression)

        self.n_expr = n_expr


class Return_Statement(Statement):
    def __init__(self, t_kw):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value() == "return"

        self.t_kw = t_kw


class Break_Statement(Statement):
    def __init__(self, t_kw):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value() == "break"

        self.t_kw = t_kw


class Continue_Statement(Statement):
    def __init__(self, t_kw):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value() == "continue"

        self.t_kw = t_kw


class Global_Statement(Statement):
    def __init__(self, t_kw, l_names):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value() == "global"
        assert isinstance(l_names, list)
        for n_name in l_names:
            assert isinstance(n_name, Identifier)

        self.t_kw    = t_kw
        self.l_names = l_names


class Persistent_Statement(Statement):
    def __init__(self, t_kw, l_names):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value() == "persistent"
        assert isinstance(l_names, list)
        for n_name in l_names:
            assert isinstance(n_name, Identifier)

        self.t_kw    = t_kw
        self.l_names = l_names


class Import_Statement(Statement):
    def __init__(self, t_kw, l_chain):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value() == "import"
        assert isinstance(l_chain, list)
        for t_item in l_chain:
            assert isinstance(t_item, MATLAB_Token)
            assert t_item.kind == "IDENTIFIER" or \
                (t_item.kind == "OPERATOR" and t_item.value() == ".*")

        self.t_kw    = t_kw
        self.l_chain = l_chain


class Try_Statement(Statement):
    def __init__(self, t_try, n_body, t_catch, n_ident, n_handler):
        super().__init__()
        assert isinstance(t_try, MATLAB_Token)
        assert t_try.kind == "KEYWORD" and t_try.value() == "try"
        if t_catch is not None:
            isinstance(t_catch, MATLAB_Token)
            assert t_catch.kind == "KEYWORD" and t_catch.value() == "catch"
        assert isinstance(n_body, Sequence_Of_Statements)
        assert n_handler is None or isinstance(n_handler,
                                               Sequence_Of_Statements)
        assert n_ident is None or isinstance(n_ident,
                                             Identifier)
        assert n_handler is not None or n_ident is None

        self.t_try     = t_try
        self.t_catch   = t_catch
        self.n_body    = n_body
        self.n_ident   = n_ident
        self.n_handler = n_handler


class Literal(Expression):
    pass


class Number_Literal(Literal):
    def __init__(self, t_value):
        super().__init__()
        assert isinstance(t_value, MATLAB_Token)
        assert t_value.kind == "NUMBER"

        self.t_value = t_value

    def __str__(self):
        return self.t_value.value()


class Char_Array_Literal(Literal):
    def __init__(self, t_string):
        super().__init__()
        assert isinstance(t_string, MATLAB_Token)
        assert t_string.kind in ("CARRAY", "BANG")

        self.t_string = t_string

    def __str__(self):
        return "'" + self.t_string.value() + "'"


class String_Literal(Literal):
    def __init__(self, t_string):
        super().__init__()
        assert isinstance(t_string, MATLAB_Token)
        assert t_string.kind == "STRING"

        self.t_string = t_string

    def __str__(self):
        return '"' + self.t_string.value() + '"'


class Unary_Operation(Expression):
    def __init__(self, precedence, t_op, n_expr):
        super().__init__()
        assert 1 <= precedence <= 12
        assert isinstance(t_op, MATLAB_Token)
        assert t_op.kind == "OPERATOR"
        assert t_op.value() in ("+", "-", "~", ".'", "'")
        assert isinstance(n_expr, Expression)

        self.precedence = precedence
        self.t_op   = t_op
        self.n_expr = n_expr

    def __str__(self):
        return "%s%s" % (self.t_op.value(), self.n_expr)


class Binary_Operation(Expression):
    def __init__(self, precedence, t_op, n_lhs, n_rhs):
        super().__init__()
        assert 1 <= precedence <= 12
        assert isinstance(t_op, MATLAB_Token)
        assert t_op.kind == "OPERATOR"
        assert isinstance(n_lhs, Expression)
        assert isinstance(n_rhs, Expression)

        self.precedence = precedence
        self.t_op  = t_op
        self.n_lhs = n_lhs
        self.n_rhs = n_rhs

    def __str__(self):
        return "(%s %s %s)" % (self.n_lhs, self.t_op.value(), self.n_rhs)


class Lambda_Function(Expression):
    def __init__(self, t_at, l_parameters, n_body):
        super().__init__()
        assert isinstance(t_at, MATLAB_Token)
        assert t_at.kind == "AT"
        assert isinstance(l_parameters, list)
        for param in l_parameters:
            assert isinstance(param, Identifier)
        assert isinstance(n_body, Expression)

        self.t_at         = t_at
        self.l_parameters = l_parameters
        self.n_body       = n_body

    def __str__(self):
        return "@(%s) %s" % (",".join(map(str, self.l_parameters)),
                             str(self.n_body))


class Function_Pointer(Expression):
    def __init__(self, t_at, n_name):
        super().__init__()
        assert isinstance(t_at, MATLAB_Token)
        assert t_at.kind == "AT"
        assert isinstance(n_name, Name)

        self.t_at   = t_at
        self.n_name = n_name

    def __str__(self):
        return "@" + str(self.n_name)


class Metaclass(Expression):
    def __init__(self, t_mc, n_name):
        super().__init__()
        assert isinstance(t_mc, MATLAB_Token)
        assert t_mc.kind == "METACLASS"
        assert isinstance(n_name, Name)

        self.t_mc   = t_mc
        self.n_name = n_name

    def __str__(self):
        return "?" + str(self.n_name)
