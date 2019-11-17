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

import os
import re

import errors

# The 1999 technical report "The Design and Implementation of a Parser
# and Scanner for the MATLAB Language in the MATCH Compiler" is a key
# piece of work that this lexer is based on. You can find a copy at:
#
# http://www.ece.northwestern.edu/cpdc/pjoisha/MAGICA/CPDC-TR-9909-017.pdf

#
# TODO: This lexer does not yet implement all the fine details. In
# particular the matrix processing is definitely wrong. But it's good
# enough to get started.
#

#
# Q: Why no PLY based lexer?
#
# A: Well, the single quote character fucks up everything. The kind of
# tricks the technical report above employes cannot be reasonably used
# in PLY. How to do this well is an open question.
#

TOKEN_KINDS = frozenset([
    "NEWLINE",
    "CONTINUATION",
    "COMMENT",
    "IDENTIFIER",
    "NUMBER",
    "STRING",
    "KEYWORD",
    "OPERATOR",
    "COMMA",
    "SEMICOLON",
    "COLON",
    "BRA", "KET",
    "C_BRA", "C_KET",
    "S_BRA", "S_KET",
    "ASSIGNMENT",
    "SELECTION"
])

TOKENS_WITH_IMPLICIT_VALUE = frozenset([
    "COMMA",
    "SEMICOLON",
    "COLON",
    "BRA", "KET",
    "C_BRA", "C_KET",
    "S_BRA", "S_KET",
    "ASSIGNMENT",
    "SELECTION"
])


# As of MATLAB 2019b
# See: https://www.mathworks.com/help/matlab/ref/iskeyword.html
KEYWORDS = frozenset([
    'break',
    'case',
    'catch',
    'classdef',
    'continue',
    'else',
    'elseif',
    'end',
    'for',
    'function',
    'global',
    'if',
    'otherwise',
    'parfor',
    'persistent',
    'return',
    'spmd',
    'switch',
    'try',
    'while',
])


class Token:
    def __init__(self, kind, raw_text):
        assert kind in TOKEN_KINDS
        assert isinstance(raw_text, str)

        self.anonymous = True
        self.kind      = kind
        self.raw_text  = raw_text

    def value(self):
        if self.kind in TOKENS_WITH_IMPLICIT_VALUE:
            return None
        elif self.kind == "CONTINUATION":
            return self.raw_text[3:].strip()
        elif self.kind == "COMMENT":
            return self.raw_text[1:].strip()
        elif self.kind == "STRING":
            return self.raw_text[1:-1]
        else:
            return self.raw_text

    def __repr__(self):
        return "Token(%s, %s)" % (self.kind, repr(self.raw_text))

    def print_message(self, message):
        raise ICE("attempting to raise error on anonymous token")


class MATLAB_Token(Token):
    def __init__(self,
                 kind,
                 raw_text,
                 filename,
                 line,
                 col_start,
                 col_end,
                 context,
                 first_in_line):
        super().__init__(kind, raw_text)
        assert isinstance(filename, str)
        assert isinstance(line, int) and line >= 1
        assert isinstance(col_start, int) and col_start >= 0
        assert isinstance(col_end, int) and (col_end >= col_start or
                                             kind == "NEWLINE")
        assert isinstance(context, str) and (len(context) > col_end or
                                             kind == "NEWLINE")
        assert isinstance(first_in_line, bool)

        self.anonymous     = False
        self.filename      = filename
        self.line          = line
        self.col_start     = col_start
        self.col_end       = col_end
        self.context       = context
        self.first_in_line = first_in_line

    def print_message(self, message):
        print("In %s, line %u" % (self.filename, self.line))
        print("| " + self.context.replace("\t", " "))
        print("| " +
              (" " * self.col_start) +
              ("^" * len(self.raw_text)) +
              " " + message)


class MATLAB_Lexer:
    def __init__(self, filename, encoding="utf-8"):
        assert isinstance(filename, str)

        if not os.path.exists(filename):
            raise errors.Anonymous_Parse_Error(filename, 0,
                                               "file does not exist")

        if not os.path.isfile(filename):
            raise errors.Anonymous_Parse_Error(filename, 0,
                                               "is not a file")

        with open(filename, "r", encoding=encoding) as fd:
            self.text = fd.read() + "\0"
        self.context_line = self.text.splitlines()

        self.filename = filename
        self.lexpos = -1
        self.line = 1
        self.col = -1
        self.matrix_stack = []
        self.first_in_line = True

        self.last_kind = None
        self.last_value = None

    def next(self):
        if self.lexpos >= 0 and self.text[self.lexpos] == "\n":
            self.col = -1
        self.lexpos += 1
        self.col += 1
        return self.text[self.lexpos]

    def advance(self, n):
        assert isinstance(n, int) and n >= 0
        for i in range(n):
            self.next()

    def match_re(self, regex):
        m = re.match("^" + regex,
                     self.text[self.lexpos:])
        if m is None:
            return None
        else:
            return m.group(0)

    def cc(self):
        return self.text[self.lexpos]

    def nc(self):
        if self.lexpos + 1 >= len(self.text):
            return "\0"
        else:
            return self.text[self.lexpos + 1]

    def nnc(self):
        if self.lexpos + 2 >= len(self.text):
            return "\0"
        else:
            return self.text[self.lexpos + 2]

    def token(self):
        def lex_error():
            raise errors.Anonymous_Parse_Error(
                self.filename,
                self.line,
                "unexpected character %s" %
                repr(self.text[self.lexpos]))

        # First we scan to the next non-whitespace token
        preceeding_ws = False
        while True:
            if self.next() not in (" ", "\t"):
                break
            preceeding_ws = True

        t_start = self.lexpos
        col_start = self.col

        # print("Begin lexing @ %u:%u <%s>" % (self.line,
        #                                      self.col,
        #                                      repr(self.cc())))

        if self.cc() == "%":
            # Comments go until the end of the line
            kind = "COMMENT"
            while self.nc() not in ("\n", "\0"):
                self.next()

        elif self.cc() == "\n":
            # Newlines are summarised into one token
            kind = "NEWLINE"
            while self.nc() == "\n":
                self.next()

        elif self.cc() == "." and self.nc() == ".":
            # This is a continuation
            kind = "CONTINUATION"
            self.next()
            if self.next() != ".":
                lex_error()

        elif self.cc().isalpha():
            # Could be an identifier or keyword
            kind = "IDENTIFIER"
            while self.nc().isalnum() or self.nc() == "_":
                self.next()

        elif self.cc().isnumeric() or \
             self.cc() == "." and self.nc().isnumeric():
            # Its some kind of number
            kind = "NUMBER"
            tmp = self.match_re(r"[0-9]*(\.[0-9]+)?([eE][+-]?[0-9]+)?")
            self.advance(len(tmp) - 1)

            # We need to make sure we now have something that isn't a
            # number to stop stupidity like 1.1.1
            if self.nc().isnumeric() or \
               self.nc() == "." and self.nnc().isnumeric():
                lex_error()

        elif self.cc() in ("<", ">", "=", "~"):
            # This is either a boolean relation, negation, or the
            # assignment
            if self.nc() == "=":
                self.next()
                kind = "OPERATOR"
            elif self.cc() == "=":
                kind = "ASSIGNMENT"
            else:
                kind = "OPERATOR"

        elif self.cc() in ("+", "-", "*", "/", "^", "\\"):
            kind = "OPERATOR"

        elif self.cc() in ("&", "|"):
            kind = "OPERATOR"
            if self.nc() == self.cc():
                self.next()

        elif self.cc() == "." and self.nc() in ("*", "/", "\\", "^", "'"):
            kind = "OPERATOR"
            self.next()

        elif self.cc() == "'":
            # This is either a single-quoted string or the transpose
            # operation. If we had preceeding whitespace, it is never
            # transpose. Otherwise it depends on bracket nesting level
            # and/or the previous token. At this point I'd like to
            # express a heartfelt THANK YOU to the MATLAB language
            # designers for this feature. If you need more ideas, wny
            # not permit unicode (including LTR, skin-tone modifiers
            # and homonyms for space) in MATLAB variable names as
            # well? Seriously, what is wrong with you people?
            kind = None
            if preceeding_ws or self.first_in_line:
                kind = "STRING"
            elif self.last_kind in ("IDENTIFIER", "NUMBER", "STRING",
                                    "KET", "S_KET", "C_KET"):
                kind = "OPERATOR"
            elif self.last_kind in ("BRA", "S_BRA", "C_BRA"):
                kind = "STRING"
            elif self.last_kind == "OPERATOR" and self.last_value == "'":
                kind = "OPERATOR"
            else:
                lex_error()

            if kind == "STRING":
                while self.nc() != "'":
                    self.next()
                    if self.cc() in ("\n", "\0"):
                        lex_error()
                self.next()

        elif self.cc() == ",":
            kind = "COMMA"

        elif self.cc() == ";":
            kind = "SEMICOLON"

        elif self.cc() == ":":
            kind = "COLON"

        elif self.cc() == "(":
            kind = "BRA"

        elif self.cc() == ")":
            kind = "KET"

        elif self.cc() == "{":
            kind = "C_BRA"

        elif self.cc() == "}":
            kind = "C_KET"

        elif self.cc() == "[":
            kind = "S_BRA"

        elif self.cc() == "]":
            kind = "S_KET"

        elif self.cc() == ".":
            kind = "SELECTION"

        elif self.cc() == "\0":
            return None

        else:
            lex_error()

        t_end = self.lexpos
        col_end = self.col
        raw_text = self.text[t_start:t_end+1]

        # print("Ended lexing @ %u:%u <%s>" % (self.line,
        #                                      self.col,
        #                                      repr(self.cc())))

        if kind == "IDENTIFIER" and raw_text in KEYWORDS:
            kind = "KEYWORD"

        token = MATLAB_Token(kind,
                             raw_text,
                             self.filename,
                             self.line,
                             col_start,
                             col_end,
                             self.context_line[self.line - 1],
                             self.first_in_line)
        self.first_in_line = False

        if kind == "NEWLINE":
            self.line += len(token.raw_text)
            self.first_in_line = True

        self.last_kind = kind
        self.last_value = raw_text

        return token


def sanity_test():
    l = MATLAB_Lexer("tests/lexer/lexing_test.m")

    while True:
        t = l.token()
        if t is None:
            break
        else:
            print(t)


if __name__ == "__main__":
    sanity_test()
