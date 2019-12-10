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

from m_lexer import Token_Generator, MATLAB_Lexer, TOKEN_KINDS
from errors import ICE, Error, Location, Message_Handler
import tree_print

# pylint: disable=wildcard-import,unused-wildcard-import
from m_ast import *
# pylint: enable=wildcard-import,unused-wildcard-import


IGNORED_TOKENS = frozenset(["COMMENT"])


class NIY(ICE):
    def __init__(self):
        super().__init__("not implemented yet")


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
        #             | reference '.' identifier
        #             | reference '(' expression_list ')'
        #             | reference '{' expression_list '}'

        rv = self.parse_identifier(allow_void)

        while self.peek("SELECTION") or self.peek("BRA") or self.peek("C_BRA"):
            if self.peek("SELECTION"):
                self.match("SELECTION")
                tok = self.ct
                field = self.parse_identifier(allow_void=False)
                rv = Selection(tok, rv, field)
            elif self.peek("BRA"):
                rv = Reference(rv, self.parse_argument_list())
            elif self.peek("C_BRA"):
                rv = Cell_Reference(rv, self.parse_cell_argument_list())
            else:
                raise ICE("impossible path (nt.kind = %s)" % self.nt.kind)

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

    def parse_file_input(self):
        while self.peek("NEWLINE"):
            self.next()

        if self.peek("KEYWORD", "function"):
            return self.parse_function_file()
        elif self.peek("KEYWORD", "classdef"):
            return self.parse_class_file()
        else:
            return self.parse_script_file()

    def parse_script_file(self):
        statements = []

        while not self.peek_eof():
            statements.append(self.parse_statement())

        return Sequence_Of_Statements(statements)

    def parse_class_file(self):
        the_class = self.parse_classdef()
        functions = self.parse_function_file()

    def parse_function_file(self):
        functions = []

        while self.peek("KEYWORD", "function"):
            fdef = self.parse_function_def()
            functions.append(fdef)

        self.match_eof()

        return functions

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

        # Some debug output for now
        tree_print.dotpr(str(rv.n_name) + ".dot", rv)

        return rv

    def parse_class_property_list(self):
        properties = []
        if self.peek("BRA"):
            self.match("BRA")
            while True:
                self.match("IDENTIFIER")
                # self.mh.info(self.ct.location,
                #              "class attributes are currently ignored")
                if self.peek("ASSIGNMENT"):
                    self.match("ASSIGNMENT")
                    self.parse_expression()
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
        attributes = self.parse_class_property_list()
        self.match("NEWLINE")

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

        self.match("KEYWORD", "end")
        self.match("NEWLINE")

        return []

    def parse_class_methods(self):
        # Using:
        # https://uk.mathworks.com/help/matlab/matlab_oop/specifying-methods-and-functions.html
        # https://uk.mathworks.com/help/matlab/matlab_oop/method-attributes.html

        self.match("KEYWORD", "methods")

        attributes = self.parse_class_property_list()
        self.match("NEWLINE")

        methods = []
        while self.peek("KEYWORD", "function"):
            methods.append(self.parse_function_def())

        self.match("KEYWORD", "end")
        self.match("NEWLINE")

        return []

    def parse_enumeration(self):
        # Using:
        # https://uk.mathworks.com/help/matlab/matlab_oop/enumerations.html

        self.match("KEYWORD", "enumeration")
        self.match("NEWLINE")

        enums = []
        while not self.peek("KEYWORD", "end"):
            name = self.parse_identifier(allow_void=False)
            if self.peek("BRA"):
                self.match("BRA")
                while True:
                    self.parse_expression()
                    if self.peek("COMMA"):
                        self.match("COMMA")
                    else:
                        break
                self.match("KET")

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

        return []

    def parse_classdef(self):
        # Using the syntax described in
        # https://uk.mathworks.com/help/matlab/matlab_oop/user-defined-classes.html
        # https://uk.mathworks.com/help/matlab/matlab_oop/class-components.html

        self.match("KEYWORD", "classdef")

        # Class attributes. Ignored for now.
        attributes = self.parse_class_property_list()

        # Class name
        class_name = self.parse_identifier(allow_void=False)

        # Inheritance
        superclasses = []
        if self.peek("OPERATOR", "<"):
            self.match("OPERATOR", "<")

            while True:
                sc_name = self.parse_simple_name()
                superclasses.append(sc_name)
                if self.peek("OPERATOR", "&"):
                    self.match("OPERATOR", "&")
                else:
                    break

        self.match("NEWLINE")

        properties = []
        methods = []
        events = []
        enumeration = []

        while True:
            if self.peek("KEYWORD", "properties"):
                properties += self.parse_class_properties()
            elif self.peek("KEYWORD", "methods"):
                methods += self.parse_class_methods()
            elif self.peek("KEYWORD", "events"):
                raise NIY()
            elif self.peek("KEYWORD", "enumeration"):
                enumeration += self.parse_enumeration()
            elif self.peek("KEYWORD", "end"):
                break
            else:
                self.mh.error(self.nt.location,
                              "expected properties|methods|events|enumeration"
                              " inside classdef")

        self.match("KEYWORD", "end")
        self.match("NEWLINE")

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
            else:
                self.mh.error(self.nt.location,
                              "expected for|if|global|while|return,"
                              " found %s instead" % self.nt.value())

        else:
            return self.parse_assignment_or_call()

    def parse_assignment_or_call(self):
        # Assignment
        #   reference "=" expr                   '<ref> = <expr>'
        #   s_assignee_matrix "=" expr           '[<ref>] = <expr>'
        #   m_assignee_matrix "=" reference      '[<ref>, <ref>] = <ref>'
        # Call
        #   potato();                            '<ref>'
        #
        # TODO: need to make sure the call case has brackets.

        lhs = []
        if self.peek("A_BRA"):
            self.match("A_BRA")
            while True:
                lhs.append(self.parse_name(allow_void=True))
                if self.peek("COMMA"):
                    self.match("COMMA")
                else:
                    break
            self.match("A_KET")
        else:
            lhs.append(self.parse_name(allow_void=False))

        # This is the call case
        if len(lhs) == 1 and not self.peek("ASSIGNMENT"):
            if self.peek("SEMICOLON"):
                self.match("SEMICOLON")
                if self.peek("NEWLINE"):
                    self.match("NEWLINE")
            else:
                # TODO: Flag style issue
                self.match("NEWLINE")
            return Naked_Expression_Statement(lhs[0])

        self.match("ASSIGNMENT")
        t_eq = self.ct

        assert len(lhs) >= 1
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

        elif self.peek("COLON"):
            self.match("COLON")
            return Reshape(self.ct)

        else:
            return self.parse_name(allow_void=False)

    # 2. Transpose (.'), power (.^), complex conjugate transpose ('),
    #    matrix power (^)
    def parse_precedence_2(self):
        # TODO: fix chaining
        lhs = self.parse_precedence_1()

        if self.peek("OPERATOR") and self.nt.value() in ("'", ".'"):
            self.match("OPERATOR")
            return Unary_Operation(2, self.ct, lhs)

        elif self.peek("OPERATOR") and self.nt.value() in ("^", ".^"):
            self.match("OPERATOR")
            t_op = self.ct
            rhs = self.parse_precedence_1()
            return Binary_Operation(2, t_op, lhs, rhs)

        else:
            return lhs

    # 3. Power with unary minus (.^-), unary plus (.^+), or logical
    #    negation (.^~) as well as matrix power with unary minus (^-), unary
    #    plus (^+), or logical negation (^~).
    #
    #    Note: Although most operators work from left to right, the
    #    operators (^-), (.^-), (^+), (.^+), (^~), and (.^~) work from
    #    second from the right to left. It is recommended that you use
    #    parentheses to explicitly specify the intended precedence of
    #    statements containing these operator combinations.
    def parse_precedence_3(self):
        # TODO: actually implement this
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

    def parse_matrix_row(self, required_elements=None):
        assert required_elements is None or required_elements >= 1
        rv = []

        if required_elements:
            for i in range(required_elements):
                if i > 0:
                    self.match("COMMA")
                rv.append(self.parse_expression())
        else:
            while not (self.peek("SEMICOLON") or
                       self.peek("NEWLINE") or
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
        dim_x = len(rows[0])

        while not (self.peek("SEMICOLON") or
                   self.peek("NEWLINE") or
                   self.peek("M_KET")):
            rows.append(self.parse_matrix_row(dim_x))
            if self.peek("SEMICOLON"):
                self.match("SEMICOLON")
            if self.peek("NEWLINE"):
                self.match("NEWLINE")

        self.match("M_KET")
        t_close = self.ct

        rv = Matrix_Expression(t_open, t_close, rows)
        return rv

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
        self.match("NEWLINE")
        n_body = self.parse_delimited_input()
        actions.append((t_kw, n_expr, n_body))

        while self.peek("KEYWORD", "elseif"):
            self.match("KEYWORD", "elseif")
            t_kw = self.ct
            n_expr = self.parse_expression()
            self.match("NEWLINE")
            n_body = self.parse_delimited_input()
            actions.append((t_kw, n_expr, n_body))

        if self.peek("KEYWORD", "else"):
            self.match("KEYWORD", "else")
            t_kw = self.ct
            self.match("NEWLINE")
            n_body = self.parse_delimited_input()
            actions.append((t_kw, None, n_body))

        self.match("KEYWORD", "end")
        self.match("NEWLINE")

        return If_Statement(actions)

    def parse_return_statement(self):
        self.match("KEYWORD", "return")
        t_kw = self.ct
        if self.peek("SEMICOLON"):
            self.match("SEMICOLON")
        self.match("NEWLINE")

        return Return_Statement(t_kw)

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

        return Global_Statement(t_global, global_names)


def sanity_test(mh, filename, show_bt):
    try:
        mh.register_file(filename)
        parser = MATLAB_Parser(mh, MATLAB_Lexer(mh, filename))
        parser.parse_file_input()
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
    options = ap.parse_args()

    mh = Message_Handler()
    mh.sort_messages = False
    mh.colour = False

    sanity_test(mh, options.file, not options.no_tb)

    mh.summary_and_exit()


if __name__ == "__main__":
    parser_test_main()
