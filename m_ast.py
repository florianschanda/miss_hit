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

class Node:
    def dump(indent=0):
        pass

class Expression(Node):
    pass

class Sequence_Of_Statements(Node):
    def __init__(self, statements):
        assert isinstance(statements, list)
        for statement in statements:
            assert isinstance(statement, Statement)
        self.statements = statements

class Statement(Node):
    pass

class Identifier(Expression):
    def __init__(self, t_ident):
        assert isinstance(t_ident, MATLAB_Token)
        assert t_ident.kind == "IDENTIFIER"

        self.t_ident = t_ident;

    def dump(indent=0):
        print (" " * (indent * 2), "Identifier(%s)" % self.t_ident.value())


class Range_Expression(Expression):
    def __init__(self, n_first, n_last, n_stride=None):
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

    def dump(indent=0):
        print (" " * (indent * 2), "Range_Expreesion")
        print (" " * (indent * 2), "First")


class Simple_For_Statement(Statement):
    def __init__(self, t_for, n_ident, n_range, n_body):
        assert isinstance(t_for, MATLAB_Token)
        assert t_for.kind == "KEYWORD" and t_for.value() == "for"
        assert isinstance(n_ident, Identifier)
        assert isinstance(n_range, Range_Expression)
        assert isinstance(n_body, Sequence_Of_Statements);

        self.t_for   = t_for
        self.n_ident = n_ident
        self.n_range = n_range
        self.n_body  = n_body

class If_Statement(Statement):
    def __init__(self, actions):
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

class Simple_Assignment_Statement(Statement):
    def __init__(self, t_eq, n_lhs, n_rhs):
        assert isinstance(t_eq, MATLAB_Token)
        assert isinstance(n_lhs, Reference)
        assert isinstance(n_rhs, Expression)

        self.t_eq  = t_eq
        self.n_lhs = n_lhs
        self.n_rhs = n_rhs

class Return_Statement(Statement):
    def __init__(self, t_kw):
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value() == "return"

        self.t_kw = t_kw

class Reference(Expression):
    def __init__(self, n_ident, arglist):
        assert isinstance(n_ident, Identifier)
        assert isinstance(arglist, list)
        for arg in arglist:
            assert isinstance(arg, Expression)

        self.n_ident = n_ident
        self.arglist = arglist

class Literal(Expression):
    pass

class String_Literal(Literal):
    def __init__(self, t_string):
        assert isinstance(t_string, MATLAB_Token)
        assert t_string.kind == "STRING"

        self.t_string = t_string

class Unary_Operation(Expression):
    def __init__(self, precedence, t_op, n_expr):
        assert 1 <= precedence <= 12
        assert isinstance(t_op, MATLAB_Token)
        assert t_op.kind == "OPERATOR"
        assert t_op.value() in ("+", "-", "~", ".'", "'")
        assert isinstance(n_expr, Expression)

        self.precedence = precedence
        self.t_op   = t_op
        self.n_expr = n_expr

class Binary_Operation(Expression):
    def __init__(self, precedence, t_op, n_lhs, n_rhs):
        assert 1 <= precedence <= 12
        assert isinstance(t_op, MATLAB_Token)
        assert t_op.kind == "OPERATOR"
        assert isinstance(n_lhs, Expression)
        assert isinstance(n_rhs, Expression)

        self.precedence = precedence
        self.t_op  = t_op
        self.n_lhs = n_lhs
        self.n_rhs = n_rhs
