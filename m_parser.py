#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2019, Florian Schanda                         ##
##              Copyright (C) 2019, Zenuity AB                              ##
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

import traceback
import subprocess

from m_lexer import Token_Generator, MATLAB_Lexer, TOKEN_KINDS
from errors import ICE, Error, Location, Message_Handler
import tree_print

# pylint: disable=wildcard-import,unused-wildcard-import
from m_ast import *
# pylint: enable=wildcard-import,unused-wildcard-import


IGNORED_TOKENS = frozenset(["COMMENT"])


# Operator precedence as of MATLAB 2019b
# https://www.mathworks.com/help/matlab/matlab_prog/operator-precedence.html
#
# 1. Parentheses ()
#
# 2. Transpose (.'), power (.^), complex conjugate transpose ('),
#    matrix power (^)
#
# 3. Power with unary minus (.^-), unary plus (.^+), or logical
#    negation (.^~) as well as matrix power with unary minus (^-), unary
#    plus (^+), or logical negation (^~).
#
#    Note: Although most operators work from left to right, the
#    operators (^-), (.^-), (^+), (.^+), (^~), and (.^~) work from
#    second from the right to left. It is recommended that you use
#    parentheses to explicitly specify the intended precedence of
#    statements containing these operator combinations.
#
# 4. Unary plus (+), unary minus (-), logical negation (~)
#
# 5. Multiplication (.*), right division (./), left division (.\),
#    matrix multiplication (*), matrix right division (/), matrix left
#    division (\)
#
# 6. Addition (+), subtraction (-)
#
# 7. Colon operator (:)
#
# 8. Less than (<), less than or equal to (<=), greater than (>),
#    greater than or equal to (>=), equal to (==), not equal to (~=)
#
# 9. Element-wise AND (&)
#
# 10. Element-wise OR (|)
#
# 11. Short-circuit AND (&&)
#
# 12. Short-circuit OR (||)

class MATLAB_Parser:
    def __init__(self, mh, lexer):
        assert isinstance(lexer, Token_Generator)
        self.lexer = lexer
        self.mh = mh

        # pylint: disable=invalid-name
        self.ct = None
        self.nt = None
        # pylint: enable=invalid-name

        self.debug_tree = False

        self.next()

    def next(self):
        self.ct = self.nt
        self.nt = self.lexer.token()

        while self.nt:
            # Skip comments and continuations
            while self.nt and self.nt.kind in ("COMMENT", "CONTINUATION"):
                self.nt = self.lexer.token()

            # Join new-lines
            if (self.nt and
                self.ct and
                self.nt.kind == "NEWLINE" and
                self.ct.kind == "NEWLINE"):
                self.nt = self.lexer.token()
            else:
                break

    def match(self, kind, value=None):
        assert kind in TOKEN_KINDS
        self.next()
        if self.ct is None:
            self.mh.error(Location(self.lexer.filename),
                          "expected %s, reached EOF instead" % kind)
        elif self.ct.kind != kind:
            if value:
                self.mh.error(self.ct.location,
                              "expected %s(%s), found %s instead" %
                              (kind, value, self.ct.kind))
            else:
                self.mh.error(self.ct.location,
                              "expected %s, found %s instead" % (kind,
                                                                 self.ct.kind))

        elif value and self.ct.value() != value:
            self.mh.error(self.ct.location,
                          "expected %s(%s), found %s(%s) instead" %
                          (kind, value, self.ct.kind, self.ct.value()))

    def match_eof(self):
        self.next()
        if self.ct is not None:
            self.mh.error(self.ct.location,
                          "expected end of file, found %s instead" %
                          self.ct.kind)

    def peek(self, kind, value=None):
        assert kind in TOKEN_KINDS
        if self.nt and self.nt.kind == kind:
            if value is None:
                return True
            else:
                return self.nt.value() == value
        else:
            return False

    def peek_eof(self):
        return self.nt is None

    ##########################################################################
    # Parsing

    def parse_identifier(self, allow_void):
        # identifier ::= <IDENTIFIER>
        #
        # void_or_identifier ::= identifier
        #                      | '~'
        if self.peek("OPERATOR", "~") and allow_void:
            self.match("OPERATOR")
            return Identifier(self.ct)
        elif self.peek("KEYWORD", "end"):
            self.match("KEYWORD", "end")
            return Identifier(self.ct)
        else:
            self.match("IDENTIFIER")
            return Identifier(self.ct)

    def parse_name(self, allow_void):
        # reference ::= identifier
        #             | identifier '@' reference
        #             | reference '.' identifier
        #             | reference '.' '(' expression ')'
        #             | reference '(' expression_list ')'
        #             | reference '{' expression_list '}'

        rv = self.parse_identifier(allow_void)

        if self.peek("AT"):
            self.match("AT")
            t_at = self.ct
            at_prefix = rv
            rv = self.parse_identifier(allow_void=False)
        else:
            t_at = None

        while self.peek("SELECTION") or self.peek("BRA") or self.peek("C_BRA"):
            if self.peek("SELECTION"):
                self.match("SELECTION")
                tok = self.ct

                if self.peek("BRA"):
                    self.match("BRA")
                    dyn_field = self.parse_expression()
                    self.match("KET")
                    rv = Dynamic_Selection(tok, rv, dyn_field)
                else:
                    field = self.parse_identifier(allow_void=False)
                    rv = Selection(tok, rv, field)
            elif self.peek("BRA"):
                rv = Reference(rv, self.parse_argument_list())
            elif self.peek("C_BRA"):
                rv = Cell_Reference(rv, self.parse_cell_argument_list())
            else:
                raise ICE("impossible path (nt.kind = %s)" % self.nt.kind)

        if t_at:
            rv = Superclass_Reference(t_at, at_prefix, rv)

        return rv

    def parse_simple_name(self):
        # reference ::= identifier
        #             | reference '.' identifier

        rv = self.parse_identifier(allow_void=False)

        while self.peek("SELECTION"):
            if self.peek("SELECTION"):
                self.match("SELECTION")
                tok = self.ct
                field = self.parse_identifier(allow_void=False)
                rv = Selection(tok, rv, field)
            else:
                raise ICE("impossible path (nt.kind = %s)" % self.nt.kind)

        return rv

    def parse_file(self):
        # This is the top-level parse function. First we need to
        # figure out exactly what kind of file we're dealing with.
        while self.peek("NEWLINE"):
            self.next()

        if self.peek("KEYWORD", "function"):
            self.parse_function_file()
        elif self.peek("KEYWORD", "classdef"):
            self.parse_class_file()
        else:
            self.parse_script_file()

    def parse_script_file(self):
        statements = []
        functions = []

        while not self.peek_eof():
            if self.peek("KEYWORD", "function"):
                break
            else:
                statements.append(self.parse_statement())

        if self.peek("KEYWORD", "function"):
            while not self.peek_eof():
                if not self.peek("KEYWORD", "function"):
                    break
                functions.append(self.parse_function_def())

        self.match_eof()

        return Sequence_Of_Statements(statements)

    def parse_class_file(self):
        self.parse_classdef()
        self.parse_function_file()

    def parse_function_file(self):
        while self.peek("KEYWORD", "function"):
            self.parse_function_def()

        self.match_eof()

    def parse_function_def(self):
        self.match("KEYWORD", "function")
        t_fun = self.ct

        # Parse returns. Either 'x' or a list '[x, y]'
        returns = []
        if self.peek("A_BRA"):
            out_brackets = True
            self.match("A_BRA")
            if self.peek("A_KET"):
                self.match("A_KET")
            else:
                while True:
                    returns.append(self.parse_identifier(allow_void=True))
                    if self.peek("COMMA"):
                        self.match("COMMA")
                    else:
                        break
                self.match("A_KET")
        else:
            out_brackets = False
            returns.append(self.parse_simple_name())

        if self.peek("BRA") and len(returns) == 1 and not out_brackets:
            # This is a function that doesn't return anything, so
            # function foo(...
            function_name = returns[0]
            returns = []

        elif self.peek("NEWLINE") and len(returns) == 1 and not out_brackets:
            # As above, but without the brackets
            function_name = returns[0]
            returns = []

        else:
            # This is a normal function, so something like
            # function [a, b] = potato...
            # function a = potato...
            self.match("ASSIGNMENT")
            function_name = self.parse_simple_name()

        inputs = []
        if self.peek("BRA"):
            self.match("BRA")
            if self.peek("KET"):
                self.match("KET")
            else:
                while True:
                    inputs.append(self.parse_identifier(allow_void=True))
                    if self.peek("COMMA"):
                        self.match("COMMA")
                    else:
                        break
                self.match("KET")

        self.match("NEWLINE")

        body = self.parse_statement_list(permit_eof=True)
        # The end+NL is gobbled by parse_statement_list

        rv = Function_Definition(t_fun, function_name, inputs, returns, body)

        if self.debug_tree:
            tree_print.dotpr("fun_" + str(rv.n_name) + ".dot", rv)
            subprocess.run(["dot", "-Tpdf",
                            "fun_" + str(rv.n_name) + ".dot",
                            "-ofun_" + str(rv.n_name) + ".pdf"])

        return rv

    def parse_class_attribute_list(self):
        properties = []

        if self.peek("BRA"):
            self.match("BRA")
            while True:
                n_name = self.parse_identifier(allow_void=False)
                if self.peek("ASSIGNMENT"):
                    self.match("ASSIGNMENT")
                    n_value = self.parse_expression()
                    properties.append(Class_Attribute(n_name, n_value))
                else:
                    properties.append(Class_Attribute(n_name))

                if self.peek("COMMA"):
                    self.match("COMMA")
                else:
                    break
            self.match("KET")

        return properties

    def parse_class_properties(self):
        # See
        # https://uk.mathworks.com/help/matlab/matlab_oop/validate-property-values.html
        # https://uk.mathworks.com/help/matlab/matlab_oop/property-validator-functions.html

        self.match("KEYWORD", "properties")
        t_kw = self.ct

        attributes = self.parse_class_attribute_list()
        self.match("NEWLINE")

        rv = Class_Block(t_kw, attributes)

        while not self.peek("KEYWORD", "end"):
            prop_name = self.parse_identifier(allow_void=False)

            # We might have validation stuff.

            # Dimension validation
            val_dim = []
            if self.peek("BRA"):
                self.match("BRA")

                while True:
                    if self.peek("NUMBER"):
                        self.match("NUMBER")
                        val_dim.append(self.ct)
                    elif self.peek("COLON"):
                        self.match("COLON")
                        val_dim.append(self.ct)
                    else:
                        self.mh.error(self.nt.location,
                                      "property dimension validation may"
                                      " contain only integral numbers or :")

                    if self.peek("COMMA"):
                        self.match("COMMA")
                    else:
                        break

                self.match("KET")

            if len(val_dim) == 1:
                self.mh.error(self.ct.location,
                              "in MATLAB dimension constraints must contain"
                              " at least two dimensions for some reason")

            # Class validation
            val_cls = None
            if self.peek("IDENTIFIER"):
                val_cls = self.parse_simple_name()

            # Function validation
            val_fun = []
            if self.peek("C_BRA"):
                self.match("C_BRA")

                while True:
                    val_fun.append(self.parse_name(allow_void=False))
                    if self.peek("COMMA"):
                        self.match("COMMA")
                    else:
                        break

                self.match("C_KET")

            # Default value
            default_value = None
            if self.peek("ASSIGNMENT"):
                self.match("ASSIGNMENT")
                default_value = self.parse_expression()

            # TODO: Style issue?
            if self.peek("SEMICOLON"):
                self.match("SEMICOLON")

            self.match("NEWLINE")

            rv.add_property(Class_Property(prop_name,
                                           val_dim,
                                           val_cls,
                                           val_fun,
                                           default_value))

        self.match("KEYWORD", "end")
        self.match("NEWLINE")

        return rv

    def parse_class_methods(self):
        # Using:
        # https://uk.mathworks.com/help/matlab/matlab_oop/specifying-methods-and-functions.html
        # https://uk.mathworks.com/help/matlab/matlab_oop/method-attributes.html

        self.match("KEYWORD", "methods")
        t_kw = self.ct

        attributes = self.parse_class_attribute_list()
        self.match("NEWLINE")

        rv = Class_Block(t_kw, attributes)

        while self.peek("KEYWORD", "function"):
            rv.add_method(self.parse_function_def())

        self.match("KEYWORD", "end")
        self.match("NEWLINE")

        return rv

    def parse_enumeration(self):
        # Using:
        # https://uk.mathworks.com/help/matlab/matlab_oop/enumerations.html

        self.match("KEYWORD", "enumeration")
        t_kw = self.ct
        self.match("NEWLINE")

        rv = Class_Block(t_kw, [])

        while not self.peek("KEYWORD", "end"):
            name = self.parse_identifier(allow_void=False)

            args = []
            if self.peek("BRA"):
                self.match("BRA")
                while True:
                    args.append(self.parse_expression())
                    if self.peek("COMMA"):
                        self.match("COMMA")
                    else:
                        break
                self.match("KET")

            rv.add_enumeration(Class_Enumeration(name, args))

            if self.peek("COMMA"):
                self.match("COMMA")
                if self.peek("NEWLINE"):
                    self.match("NEWLINE")
            elif self.peek("SEMICOLON"):
                self.match("SEMICOLON")
                if self.peek("NEWLINE"):
                    self.match("NEWLINE")
            else:
                self.match("NEWLINE")

        self.match("KEYWORD", "end")
        self.match("NEWLINE")

        return rv

    def parse_class_events(self):
        # Using the syntax described in
        # https://www.mathworks.com/help/matlab/matlab_oop/events-and-listeners.html
        self.match("KEYWORD", "events")
        t_kw = self.ct
        self.match("NEWLINE")

        rv = Class_Block(t_kw, [])

        while not self.peek("KEYWORD", "end"):
            rv.add_event(self.parse_identifier(allow_void=False))
            self.match("NEWLINE")

        self.match("KEYWORD", "end")
        self.match("NEWLINE")

        return rv

    def parse_classdef(self):
        # Using the syntax described in
        # https://uk.mathworks.com/help/matlab/matlab_oop/user-defined-classes.html
        # https://uk.mathworks.com/help/matlab/matlab_oop/class-components.html

        self.match("KEYWORD", "classdef")
        t_classdef = self.ct

        # Class attributes. Ignored for now.
        attributes = self.parse_class_attribute_list()

        # Class name
        class_name = self.parse_identifier(allow_void=False)

        # Inheritance
        l_super = []
        if self.peek("OPERATOR", "<"):
            self.match("OPERATOR", "<")

            while True:
                sc_name = self.parse_simple_name()
                l_super.append(sc_name)

                if self.peek("OPERATOR", "&"):
                    self.match("OPERATOR", "&")
                else:
                    break

        self.match("NEWLINE")

        rv = Class_Definition(t_classdef, class_name, attributes, l_super)

        while True:
            if self.peek("KEYWORD", "properties"):
                rv.add_block(self.parse_class_properties())
            elif self.peek("KEYWORD", "methods"):
                rv.add_block(self.parse_class_methods())
            elif self.peek("KEYWORD", "events"):
                rv.add_block(self.parse_class_events())
            elif self.peek("KEYWORD", "enumeration"):
                rv.add_block(self.parse_enumeration())
            elif self.peek("KEYWORD", "end"):
                break
            else:
                self.mh.error(self.nt.location,
                              "expected properties|methods|events|enumeration"
                              " inside classdef")

        self.match("KEYWORD", "end")
        self.match("NEWLINE")

        if self.debug_tree:
            tree_print.dotpr("cls_" + str(rv.n_name) + ".dot", rv)
            subprocess.run(["dot", "-Tpdf",
                            "cls_" + str(rv.n_name) + ".dot",
                            "-ocls_" + str(rv.n_name) + ".pdf"])

        return rv

    def parse_statement_list(self, permit_eof=False):
        assert isinstance(permit_eof, bool)

        statements = []

        while not (self.peek("KEYWORD", "end") or self.peek_eof()):
            statements.append(self.parse_statement())

        if permit_eof and self.peek_eof():
            # TODO: style issue
            pass
        else:
            self.match("KEYWORD", "end")
            self.match("NEWLINE")

        return Sequence_Of_Statements(statements)

    def parse_delimited_input(self):
        statements = []

        while True:
            if self.peek("KEYWORD") and self.nt.value() in ("end",
                                                            "catch",
                                                            "case",
                                                            "otherwise",
                                                            "else",
                                                            "elseif"):
                break
            statements.append(self.parse_statement())

        return Sequence_Of_Statements(statements)

    def parse_statement(self):
        if self.peek("KEYWORD"):
            if self.nt.value() == "for":
                return self.parse_for_statement()
            elif self.nt.value() == "if":
                return self.parse_if_statement()
            elif self.nt.value() == "global":
                return self.parse_global_statement()
            elif self.nt.value() == "while":
                return self.parse_while_statement()
            elif self.nt.value() == "return":
                return self.parse_return_statement()
            elif self.nt.value() == "switch":
                return self.parse_switch_statement()
            elif self.nt.value() == "break":
                return self.parse_break_statement()
            elif self.nt.value() == "continue":
                return self.parse_continue_statement()
            elif self.nt.value() == "import":
                return self.parse_import_statement()
            elif self.nt.value() == "try":
                return self.parse_try_statement()
            elif self.nt.value() == "persistent":
                return self.parse_persistent_statement()
            else:
                self.mh.error(self.nt.location,
                              "expected for|if|global|while|return|switch|"
                              "break|continue|import|try|persistent,"
                              " found %s instead" % self.nt.value())
        elif self.peek("BANG"):
            self.match("BANG")
            t_bang = self.ct
            self.match("NEWLINE")
            return Naked_Expression_Statement(
                Function_Call(Identifier(t_bang),
                              [Char_Array_Literal(t_bang)],
                              "escape"))
        elif self.peek("A_BRA"):
            return self.parse_list_assignment()
        else:
            # This can be one of three things
            # other_stmt ::= reference "=" expr # simple assignment
            #              | reference CARRAY+  # command form
            #              | expression         # naked expression, could be
            #                                   # a call
            rv = self.parse_expression()

            if self.peek("ASSIGNMENT"):
                self.match("ASSIGNMENT")
                t_eq = self.ct
                rhs = self.parse_expression()
                rv = Simple_Assignment_Statement(t_eq, rv, rhs)

            elif self.peek("CARRAY"):
                # Sanity check that the function is a simple name
                if not isinstance(rv, (Identifier, Selection)):
                    self.mh.error(self.ct.location,
                                  "command form requires a simple (dotted)"
                                  " identifier; found %s instead" %
                                  rv.__class__.__name__)

                arg_list = []
                while self.peek("CARRAY"):
                    self.match("CARRAY")
                    arg_list.append(Char_Array_Literal(self.ct))
                rv = Function_Call(rv, arg_list, "command")
                rv = Naked_Expression_Statement(rv)

            else:
                rv = Naked_Expression_Statement(rv)

            if self.peek("SEMICOLON"):
                self.match("SEMICOLON")
                if self.peek("NEWLINE"):
                    self.match("NEWLINE")
            elif self.peek("COLON"):
                # TODO: Flag style issue
                self.match("COLON")
                if self.peek("NEWLINE"):
                    self.match("NEWLINE")
            else:
                # TODO: Flag style issue
                self.match("NEWLINE")

            return rv

    def parse_list_assignment(self):
        # Assignment
        #   s_assignee_matrix "=" expr           '[<ref>] = <expr>'
        #   m_assignee_matrix "=" reference      '[<ref>, <ref>] = <ref>'

        lhs = []

        self.match("A_BRA")
        while True:
            lhs.append(self.parse_name(allow_void=True))
            if self.peek("COMMA"):
                self.match("COMMA")
            else:
                break
        self.match("A_KET")

        self.match("ASSIGNMENT")
        t_eq = self.ct

        if len(lhs) == 1:
            # We've got something like
            #    [x] = <expr>
            rhs = self.parse_expression()
        else:
            # We've got something like
            #    [x, y] = fun(...)
            #
            # I believe that this can't be an expression, it basically
            # has to be a function call. Needs to be checked.
            rhs = self.parse_name(allow_void=False)

        if self.peek("SEMICOLON"):
            self.match("SEMICOLON")
            if self.peek("NEWLINE"):
                self.match("NEWLINE")
        else:
            # TODO: Flag style issue
            self.match("NEWLINE")

        if len(lhs) == 1:
            return Simple_Assignment_Statement(t_eq, lhs[0], rhs)
        else:
            return Compound_Assignment_Statement(t_eq, lhs, rhs)

    def parse_expression(self):
        return self.parse_precedence_12()

    # 1. Parentheses ()
    def parse_precedence_1(self):
        if self.peek("NUMBER"):
            self.match("NUMBER")
            return Number_Literal(self.ct)

        elif self.peek("CARRAY"):
            self.match("CARRAY")
            return Char_Array_Literal(self.ct)

        elif self.peek("STRING"):
            self.match("STRING")
            return String_Literal(self.ct)

        elif self.peek("BRA"):
            self.match("BRA")
            expr = self.parse_expression()
            self.match("KET")
            return expr

        elif self.peek("M_BRA"):
            return self.parse_matrix()

        elif self.peek("C_BRA"):
            return self.parse_cell()

        elif self.peek("COLON"):
            self.match("COLON")
            return Reshape(self.ct)

        elif self.peek("AT"):
            return self.parse_function_handle()

        elif self.peek("METACLASS"):
            self.match("METACLASS")
            tok = self.ct
            return Metaclass(tok, self.parse_simple_name())

        else:
            return self.parse_name(allow_void=False)

    # 2. Transpose (.'), power (.^), complex conjugate transpose ('),
    #    matrix power (^)
    #
    # 3. Power with unary minus (.^-), unary plus (.^+), or logical
    #    negation (.^~) as well as matrix power with unary minus (^-), unary
    #    plus (^+), or logical negation (^~).
    #
    #    Note: Although most operators work from left to right, the
    #    operators (^-), (.^-), (^+), (.^+), (^~), and (.^~) work from
    #    second from the right to left. It is recommended that you use
    #    parentheses to explicitly specify the intended precedence of
    #    statements containing these operator combinations.
    def parse_precedence_2(self):
        # In Octave chaining ^ is left associative, i.e. 2 ^ 3 ^ 2 ==
        # (2 ^ 3) ^ 2 == 64.
        #
        # TODO: Is this also true for MATLAB?
        rv = self.parse_precedence_1()

        while self.peek("OPERATOR") and self.nt.value() in ("^", ".^",
                                                            "'", ".'"):
            self.match("OPERATOR")
            t_op = self.ct
            if t_op.value() in ("^", ".^"):
                unary_chain = []
                while self.peek("OPERATOR") and \
                      self.nt.value() in ("-", "+", "~"):
                    self.match("OPERATOR")
                    unary_chain.append(self.ct)
                rhs = self.parse_precedence_1()
                while unary_chain:
                    rhs = Unary_Operation(3, unary_chain.pop(), rhs)
                rv = Binary_Operation(2, t_op, rv, rhs)
            else:
                rv = Unary_Operation(2, t_op, rv)

        return rv

    def parse_precedence_3(self):
        # This is dealt with as a special case in (2).
        return self.parse_precedence_2()

    # 4. Unary plus (+), unary minus (-), logical negation (~)
    def parse_precedence_4(self):
        if self.peek("OPERATOR") and self.nt.value() in ("+", "-", "~"):
            self.match("OPERATOR")
            t_op = self.ct
            rhs = self.parse_precedence_4()
            return Unary_Operation(4, t_op, rhs)
        else:
            return self.parse_precedence_3()

    # 5. Multiplication (.*), right division (./), left division (.\),
    #    matrix multiplication (*), matrix right division (/), matrix left
    #    division (\)
    def parse_precedence_5(self):
        rv = self.parse_precedence_4()

        while self.peek("OPERATOR") and self.nt.value() in ("*", ".*",
                                                            "/", "./",
                                                            "\\", ".\\"):
            self.match("OPERATOR")
            t_op = self.ct
            rhs = self.parse_precedence_4()
            rv = Binary_Operation(5, t_op, rv, rhs)

        return rv

    # 6. Addition (+), subtraction (-)
    def parse_precedence_6(self):
        rv = self.parse_precedence_5()

        while self.peek("OPERATOR") and self.nt.value() in ("+", "-"):
            self.match("OPERATOR")
            t_op = self.ct
            rhs = self.parse_precedence_5()
            rv = Binary_Operation(6, t_op, rv, rhs)

        return rv

    # 7. Colon operator (:)
    def parse_range_expression(self):
        points = []
        points.append(self.parse_precedence_6())
        if self.peek("COLON"):
            self.match("COLON")
            points.append(self.parse_precedence_6())
        if self.peek("COLON"):
            self.match("COLON")
            points.append(self.parse_precedence_6())
        assert 1 <= len(points) <= 3

        if len(points) == 1:
            return points[0]
        elif len(points) == 2:
            return Range_Expression(points[0], points[1])
        else:
            return Range_Expression(points[0], points[1], points[2])

    # 8. Less than (<), less than or equal to (<=), greater than (>),
    #    greater than or equal to (>=), equal to (==), not equal to (~=)
    def parse_precedence_8(self):
        rv = self.parse_range_expression()

        while self.peek("OPERATOR") and self.nt.value() in ("<", "<=",
                                                            ">", ">=",
                                                            "==", "~="):
            self.match("OPERATOR")
            t_op = self.ct
            rhs = self.parse_range_expression()
            rv = Binary_Operation(8, t_op, rv, rhs)

        return rv

    # 9. Element-wise AND (&)
    def parse_precedence_9(self):
        rv = self.parse_precedence_8()

        while self.peek("OPERATOR", "&"):
            self.match("OPERATOR", "&")
            t_op = self.ct
            rhs = self.parse_precedence_8()
            rv = Binary_Operation(9, t_op, rv, rhs)

        return rv

    # 10. Element-wise OR (|)
    def parse_precedence_10(self):
        rv = self.parse_precedence_9()

        while self.peek("OPERATOR", "|"):
            self.match("OPERATOR", "|")
            t_op = self.ct
            rhs = self.parse_precedence_9()
            rv = Binary_Operation(10, t_op, rv, rhs)

        return rv

    # 11. Short-circuit AND (&&)
    def parse_precedence_11(self):
        rv = self.parse_precedence_10()

        while self.peek("OPERATOR", "&&"):
            self.match("OPERATOR", "&&")
            t_op = self.ct
            rhs = self.parse_precedence_10()
            rv = Binary_Operation(11, t_op, rv, rhs)

        return rv

    # 12. Short-circuit OR (||)
    def parse_precedence_12(self):
        rv = self.parse_precedence_11()

        while self.peek("OPERATOR", "||"):
            self.match("OPERATOR", "||")
            t_op = self.ct
            rhs = self.parse_precedence_11()
            rv = Binary_Operation(12, t_op, rv, rhs)

        return rv

    def parse_matrix_row(self):
        rv = []

        while not (self.peek("SEMICOLON") or
                   self.peek("NEWLINE") or
                   self.peek("C_KET") or
                   self.peek("M_KET")):
            rv.append(self.parse_expression())
            if self.peek("COMMA"):
                self.match("COMMA")

        return rv

    def parse_matrix(self):
        self.match("M_BRA")
        t_open = self.ct

        rows = [self.parse_matrix_row()]
        if self.peek("SEMICOLON"):
            self.match("SEMICOLON")
        if self.peek("NEWLINE"):
            self.match("NEWLINE")

        while not (self.peek("SEMICOLON") or
                   self.peek("NEWLINE") or
                   self.peek("M_KET")):
            rows.append(self.parse_matrix_row())
            if self.peek("SEMICOLON"):
                self.match("SEMICOLON")
            if self.peek("NEWLINE"):
                self.match("NEWLINE")

        self.match("M_KET")
        t_close = self.ct

        rv = Matrix_Expression(t_open, t_close, rows)
        return rv

    def parse_cell(self):
        self.match("C_BRA")
        t_open = self.ct

        rows = [self.parse_matrix_row()]
        if self.peek("SEMICOLON"):
            self.match("SEMICOLON")
        if self.peek("NEWLINE"):
            self.match("NEWLINE")

        while not (self.peek("SEMICOLON") or
                   self.peek("NEWLINE") or
                   self.peek("C_KET")):
            rows.append(self.parse_matrix_row())
            if self.peek("SEMICOLON"):
                self.match("SEMICOLON")
            if self.peek("NEWLINE"):
                self.match("NEWLINE")

        self.match("C_KET")
        t_close = self.ct

        rv = Cell_Expression(t_open, t_close, rows)
        return rv

    def parse_function_handle(self):
        self.match("AT")
        t_at = self.ct

        if self.peek("BRA"):
            self.match("BRA")
            lambda_args = []
            while not self.peek("KET"):
                lambda_args.append(self.parse_identifier(allow_void=False))
                if self.peek("COMMA"):
                    self.match("COMMA")
                else:
                    break
            self.match("KET")
            lambda_body = self.parse_expression()
            return Lambda_Function(t_at, lambda_args, lambda_body)
        else:
            name = self.parse_simple_name()
            return Function_Pointer(t_at, name)

    def parse_argument_list(self):
        # arglist ::= '(' ')'
        #           | '(' expression { ',' expression } '}'
        #
        # Note: This list can be empty
        args = []
        self.match("BRA")
        if self.peek("KET"):
            self.match("KET")
            return args

        while True:
            args.append(self.parse_expression())
            if self.peek("COMMA"):
                self.match("COMMA")
            elif self.peek("KET"):
                break
        self.match("KET")
        return args

    def parse_cell_argument_list(self):
        # cell_arglist ::= '{' expression { ',' expression } '}'
        #
        # Note: cannot be empty
        args = []
        self.match("C_BRA")

        while True:
            args.append(self.parse_expression())
            if self.peek("COMMA"):
                self.match("COMMA")
            elif self.peek("C_KET"):
                break

        self.match("C_KET")
        return args

    def parse_if_statement(self):
        actions = []

        self.match("KEYWORD", "if")
        t_kw = self.ct
        n_expr = self.parse_expression()
        if self.peek("SEMICOLON"):
            self.match("SEMICOLON")
        self.match("NEWLINE")
        n_body = self.parse_delimited_input()
        actions.append((t_kw, n_expr, n_body))

        while self.peek("KEYWORD", "elseif"):
            self.match("KEYWORD", "elseif")
            t_kw = self.ct
            n_expr = self.parse_expression()
            if self.peek("SEMICOLON"):
                self.match("SEMICOLON")
            self.match("NEWLINE")
            n_body = self.parse_delimited_input()
            actions.append((t_kw, n_expr, n_body))

        if self.peek("KEYWORD", "else"):
            self.match("KEYWORD", "else")
            t_kw = self.ct
            if self.peek("SEMICOLON"):
                self.match("SEMICOLON")
            self.match("NEWLINE")
            n_body = self.parse_delimited_input()
            actions.append((t_kw, None, n_body))

        self.match("KEYWORD", "end")
        if self.peek("SEMICOLON"):
            self.match("SEMICOLON")
        self.match("NEWLINE")

        return If_Statement(actions)

    def parse_return_statement(self):
        self.match("KEYWORD", "return")
        t_kw = self.ct
        if self.peek("SEMICOLON"):
            self.match("SEMICOLON")
        self.match("NEWLINE")

        return Return_Statement(t_kw)

    def parse_break_statement(self):
        self.match("KEYWORD", "break")
        t_kw = self.ct
        if self.peek("SEMICOLON"):
            self.match("SEMICOLON")
        self.match("NEWLINE")

        return Break_Statement(t_kw)

    def parse_continue_statement(self):
        self.match("KEYWORD", "continue")
        t_kw = self.ct
        if self.peek("SEMICOLON"):
            self.match("SEMICOLON")
        self.match("NEWLINE")

        return Continue_Statement(t_kw)

    def parse_for_statement(self):
        self.match("KEYWORD", "for")
        t_kw = self.ct
        n_ident = self.parse_identifier(allow_void=False)
        self.match("ASSIGNMENT")
        n_expr = self.parse_expression()

        self.match("NEWLINE")

        n_body = self.parse_delimited_input()

        self.match("KEYWORD", "end")
        self.match("NEWLINE")

        if isinstance(n_expr, Range_Expression):
            return Simple_For_Statement(t_kw, n_ident, n_expr, n_body)
        else:
            return General_For_Statement(t_kw, n_ident, n_expr, n_body)

    def parse_while_statement(self):
        self.match("KEYWORD", "while")
        t_kw = self.ct

        n_guard = self.parse_expression()
        self.match("NEWLINE")

        n_body = self.parse_delimited_input()
        self.match("KEYWORD", "end")

        self.match("NEWLINE")

        return While_Statement(t_kw, n_guard, n_body)

    def parse_global_statement(self):
        self.match("KEYWORD", "global")
        t_global = self.ct

        global_names = []
        while True:
            global_names.append(self.parse_identifier(allow_void=False))
            if self.peek("NEWLINE"):
                self.match("NEWLINE")
                break
            elif self.peek("SEMICOLON"):
                self.match("SEMICOLON")
                self.match("NEWLINE")
                break

        return Global_Statement(t_global, global_names)

    def parse_persistent_statement(self):
        self.match("KEYWORD", "persistent")
        t_kw = self.ct

        l_names = []
        while True:
            l_names.append(self.parse_identifier(allow_void=False))
            if self.peek("NEWLINE"):
                self.match("NEWLINE")
                break
            elif self.peek("SEMICOLON"):
                self.match("SEMICOLON")
                self.match("NEWLINE")
                break

        return Persistent_Statement(t_kw, l_names)

    def parse_switch_statement(self):
        self.match("KEYWORD", "switch")
        t_switch = self.ct

        n_switch_expr = self.parse_expression()
        self.match("NEWLINE")

        l_options = []
        while True:
            if self.peek("KEYWORD", "otherwise"):
                self.match("KEYWORD", "otherwise")
                t_kw = self.ct
                self.match("NEWLINE")
                n_body = self.parse_delimited_input()
                l_options.append((t_kw, None, n_body))
                break
            else:
                self.match("KEYWORD", "case")
                t_kw = self.ct
                n_expr = self.parse_expression()
                self.match("NEWLINE")
                n_body = self.parse_delimited_input()
                l_options.append((t_kw, n_expr, n_body))

            if self.peek("KEYWORD", "end"):
                break

        self.match("KEYWORD", "end")
        self.match("NEWLINE")

        return Switch_Statement(t_switch, n_switch_expr, l_options)

    def parse_import_statement(self):
        self.match("KEYWORD", "import")
        t_kw = self.ct

        self.match("IDENTIFIER")
        chain = [self.ct]
        while self.peek("SELECTION") or self.peek("OPERATOR", ".*"):
            if self.peek("OPERATOR", ".*"):
                self.match("OPERATOR", ".*")
                chain.append(self.ct)
                break
            else:
                self.match("SELECTION")
                self.match("IDENTIFIER")
                chain.append(self.ct)
        if self.peek("SEMICOLON"):
            self.match("SEMICOLON")
        self.match("NEWLINE")

        return Import_Statement(t_kw, chain)

    def parse_try_statement(self):
        self.match("KEYWORD", "try")
        t_try = self.ct
        self.match("NEWLINE")

        n_body = self.parse_delimited_input()

        self.match("KEYWORD", "catch")
        t_catch = self.ct
        if self.peek("NEWLINE"):
            n_ident = None
        else:
            n_ident = self.parse_identifier(allow_void = False)
        self.match("NEWLINE")

        n_handler = self.parse_delimited_input()

        self.match("KEYWORD", "end")
        self.match("NEWLINE")

        return Try_Statement(t_try, n_body, t_catch, n_ident, n_handler)


def sanity_test(mh, filename, show_bt, show_tree):
    try:
        mh.register_file(filename)
        parser = MATLAB_Parser(mh, MATLAB_Lexer(mh, filename))
        parser.debug_tree = show_tree
        parser.parse_file()
    except Error:
        if show_bt:
            traceback.print_exc()
    mh.finalize_file(filename)


def parser_test_main():
    from argparse import ArgumentParser
    ap = ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--no-tb",
                    action="store_true",
                    default=False,
                    help="Do not show debug-style backtrace")
    ap.add_argument("--tree",
                    action="store_true",
                    default=False,
                    help="Create parse tree with graphviz for each function")
    options = ap.parse_args()

    mh = Message_Handler()
    mh.sort_messages = False
    mh.colour = False

    sanity_test(mh, options.file, not options.no_tb, options.tree)

    mh.summary_and_exit()


if __name__ == "__main__":
    parser_test_main()
