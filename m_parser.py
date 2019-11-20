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


from errors import mh, ICE, Error
from m_lexer import Token_Generator, MATLAB_Lexer, MATLAB_Token
from m_ast import *
import tree_print

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
    def __init__(self, lexer):
        assert isinstance(lexer, Token_Generator)
        self.lexer = lexer
        self.ct = None
        self.nt = None
        self.next()

    def next(self):
        self.ct = self.nt
        self.nt = self.lexer.token()

        while self.nt:
            # Skip comments
            while self.nt and self.nt.kind == "COMMENT":
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
        self.next()
        if self.ct is None:
            mh.error(Location(lexer.filename),
                     "expected %s, reached EOF instead" % kind)
        elif self.ct.kind != kind:
            mh.error(self.ct.location,
                     "expected %s, found %s instead" % (kind, self.ct.kind))
        elif value and self.ct.value() != value:
            mh.error(self.ct.location,
                     "expected %s(%s), found %s(%s) instead" %
                     (kind, value, self.ct.kind, self.ct.value()))

    def match_eof(self):
        self.next()
        if self.ct is not None:
            mh.error(self.ct.location,
                     "expected end of file, found %s instead" % self.ct.kind)

    def peek(self, kind, value=None):
        if self.nt and self.nt.kind == kind:
            if value is None:
                return True
            else:
                return self.nt.value() == value
        else:
            return False

    ##########################################################################
    # Parsing

    def parse_identifier(self):
        self.match("IDENTIFIER")
        return Identifier(self.ct)

    def parse_file_input(self):
        while self.peek("NEWLINE"):
            self.match("NEWLINE")

        if self.peek("KEYWORD", "function"):
            return self.parse_function_file()
        else:
            return self.parse_script_file()

    def parse_script_file(self):
        raise NIY()

    def parse_function_file(self):
        functions = []

        while self.peek("KEYWORD", "function"):
            functions.append(self.parse_function_def())
            if self.peek("NEWLINE"):
                self.match("NEWLINE")

        self.match_eof()
        return functions

    def parse_function_def(self):
        self.match("KEYWORD", "function")

        # Parse returns. Either 'x' or a list '[x, y]'
        returns = []
        if self.peek("S_BRA"):
            self.match("S_BRA")
            while True:
                self.parse_identifier()
                returns.append(self.ct.value())
                if self.peek("COMMA"):
                    self.match("COMMA")
                else:
                    break
            self.match("S_KET")
        else:
            self.parse_identifier()
            returns.append(self.ct.value())

        self.match("ASSIGNMENT")
        name = self.parse_identifier()

        inputs = []
        if self.peek("BRA"):
            self.match("BRA")
            while True:
                self.parse_identifier()
                inputs.append(self.ct.value())
                if self.peek("COMMA"):
                    self.match("COMMA")
                else:
                    break
            self.match("KET")

        self.match("NEWLINE")

        body = self.parse_statement_list()
        for statement in body.statements:
            tree_print.treepr(statement)

        # TODO: Build function entity

    def parse_statement_list(self):
        statements = []

        while not self.peek("KEYWORD", "end"):
            statements.append(self.parse_statement())

        self.match("KEYWORD", "end")

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
                raise NIY()
            elif self.nt.value() == "while":
                raise NIY()
            elif self.nt.value() == "return":
                return self.parse_return_statement()
            else:
                mh.error(self.nt.location,
                         "expected for|if|global|while|return,"
                         " found %s instead" % self.nt.value())

        else:
            return self.parse_assignment()

    def parse_assignment(self):
        # Three options
        #   reference "=" expr                   '<ref> = <expr>'
        #   s_assignee_matrix "=" expr           '[<ref>] = <expr>'
        #   m_assignee_matrix "=" reference      '[<ref>, <ref>] = <ref>'

        lhs = []
        if self.peek("S_BRA"):
            self.match("S_BRA")
            while True:
                lhs.append(self.parse_reference())
                if self.peek("COMMA"):
                    self.match("COMMA")
                else:
                    break
            self.match("S_KET")
        else:
            lhs.append(self.parse_reference())

        self.match("ASSIGNMENT")
        t_eq = self.ct

        assert len(lhs) >= 1
        if len(lhs) == 1:
            rhs = self.parse_expression()
        else:
            rhs = self.parse_reference()

        self.match("SEMICOLON")
        self.match("NEWLINE")

        if len(lhs) == 1:
            return Simple_Assignment_Statement(t_eq, lhs[0], rhs)
        else:
            raise NIY()

    def parse_reference(self):
        # identifier                   'potato'
        # identifier ( arglist )       'array(12)'

        n_ident = self.parse_identifier()

        if self.peek("BRA"):
            arglist = self.parse_argument_list()
        else:
            arglist = []

        return Reference(n_ident, arglist)

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

        elif self.peek("S_BRA"):
            return self.parse_matrix()

        else:
            return self.parse_reference()

    # 2. Transpose (.'), power (.^), complex conjugate transpose ('),
    #    matrix power (^)
    def parse_precedence_2(self):
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
        # TODO
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
        lhs = self.parse_precedence_4()
        if self.peek("OPERATOR") and self.nt.value() in (".*", "./", r".\\",
                                                         "*", "/", "\\"):
            self.match("OPERATOR")
            t_op = self.ct
            rhs = self.parse_precedence_5()
            return Binary_Operation(5, t_op, lhs, rhs)
        else:
            return lhs

    # 6. Addition (+), subtraction (-)
    def parse_precedence_6(self):
        lhs = self.parse_precedence_5()
        if self.peek("OPERATOR") and self.nt.value() in ("+", "-"):
            self.match("OPERATOR")
            t_op = self.ct
            rhs = self.parse_precedence_6()
            return Binary_Operation(6, t_op, lhs, rhs)
        else:
            return lhs

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
        lhs = self.parse_range_expression()
        if self.peek("OPERATOR") and self.nt.value() in ("<", "<=", ">", ">=",
                                                         "==", "~="):
            self.match("OPERATOR")
            t_op = self.ct
            rhs = self.parse_precedence_8()
            return Binary_Operation(8, t_op, lhs, rhs)
        else:
            return lhs

    # 9. Element-wise AND (&)
    def parse_precedence_9(self):
        lhs = self.parse_precedence_8()
        if self.peek("OPERATOR", "&"):
            self.match("OPERATOR", "&")
            t_op = self.ct
            rhs = self.parse_precedence_9()
            return Binary_Operation(9, t_op, lhs, rhs)
        else:
            return lhs

    # 10. Element-wise OR (|)
    def parse_precedence_10(self):
        lhs = self.parse_precedence_9()
        if self.peek("OPERATOR", "|"):
            self.match("OPERATOR", "|")
            t_op = self.ct
            rhs = self.parse_precedence_10()
            return Binary_Operation(10, t_op, lhs, rhs)
        else:
            return lhs

    # 11. Short-circuit AND (&&)
    def parse_precedence_11(self):
        lhs = self.parse_precedence_10()
        if self.peek("OPERATOR", "|"):
            self.match("OPERATOR", "|")
            t_op = self.ct
            rhs = self.parse_precedence_11()
            return Binary_Operation(11, t_op, lhs, rhs)
        else:
            return lhs

    # 12. Short-circuit OR (||)
    def parse_precedence_12(self):
        lhs = self.parse_precedence_11()
        if self.peek("OPERATOR", "|"):
            self.match("OPERATOR", "|")
            t_op = self.ct
            rhs = self.parse_precedence_12()
            return Binary_Operation(12, t_op, lhs, rhs)
        else:
            return lhs

    def parse_matrix(self):
        raise NIY()

    def parse_argument_list(self):
        args = []
        self.match("BRA")
        while True:
            args.append(self.parse_expression())
            if self.peek("COMMA"):
                self.match("COMMA")
            else:
                break
        self.match("KET")
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
        self.match("SEMICOLON")
        self.match("NEWLINE")

        return Return_Statement(t_kw)

    def parse_for_statement(self):
        self.match("KEYWORD", "for")
        t_kw = self.ct
        n_ident = self.parse_identifier()
        self.match("ASSIGNMENT")
        n_range = self.parse_range_expression()
        self.match("NEWLINE")

        n_body = self.parse_delimited_input()

        self.match("KEYWORD", "end")
        self.match("NEWLINE")

        return Simple_For_Statement(t_kw, n_ident, n_range, n_body)

def sanity_test(filename):
    try:
        parser = MATLAB_Parser(MATLAB_Lexer(filename))
        parser.parse_file_input()
        print("%s: parsed OK" % filename)
    except Error as e:
        pass

if __name__ == "__main__":
    sanity_test("tests/parser/simple.m")
    sanity_test("tests/parser/simple_pe.m")
    mh.print_summary_and_exit()
