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

import re
from abc import ABCMeta, abstractmethod

from errors import Location, Error, mh
from m_language import KEYWORDS

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
    "DIRECTORY",
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
    "SELECTION",
    "AT",
    "BANG",
    "METACLASS",
])

TOKENS_WITH_IMPLICIT_VALUE = frozenset([
    "COMMA",
    "SEMICOLON",
    "COLON",
    "BRA", "KET",
    "C_BRA", "C_KET",
    "S_BRA", "S_KET",
    "ASSIGNMENT",
    "SELECTION",
    "AT",
    "BANG",
    "METACLASS"
])


class MATLAB_Token:
    def __init__(self,
                 kind,
                 raw_text,
                 location,
                 first_in_line,
                 anonymous = False):
        assert kind in TOKEN_KINDS
        assert isinstance(raw_text, str)
        assert isinstance(location, Location)
        assert isinstance(first_in_line, bool)
        assert isinstance(anonymous, bool)

        self.kind          = kind
        self.raw_text      = raw_text
        self.location      = location
        self.first_in_line = first_in_line
        self.anonymous     = anonymous

        # Not part of parsing, but some fix suggestions can be added
        self.fix = {}

    def value(self):
        if self.kind in TOKENS_WITH_IMPLICIT_VALUE:
            return None
        elif self.kind == "CONTINUATION":
            return self.raw_text[3:].strip()
        elif self.kind == "COMMENT":
            return self.raw_text[1:].strip()
        elif self.kind == "STRING":
            return self.raw_text[1:-1]
        elif self.kind == "DIRECTORY":
            return self.raw_text.strip()
        else:
            return self.raw_text

    def __repr__(self):
        val = self.value()
        star = "*" if self.anonymous else ""

        if val is None or self.kind == "NEWLINE":
            return "Token%s(%s)" % (star, self.kind)
        else:
            return "Token%s(%s, <<%s>>)" % (star, self.kind, val)


class Token_Generator(metaclass=ABCMeta):
    def __init__(self, filename):
        assert isinstance(filename, str)
        self.filename = filename

    @abstractmethod
    def token(self):
        pass


class MATLAB_Lexer(Token_Generator):
    def __init__(self, filename, encoding="utf-8"):
        super().__init__(filename)

        with open(filename, "r", encoding=encoding) as fd:
            self.text = fd.read()
        self.context_line = self.text.splitlines()

        self.filename = filename
        self.lexpos = -1
        self.col_offset = 0
        self.line = 1
        self.matrix_stack = []
        self.first_in_line = True
        self.in_dir_command = False

        # pylint: disable=invalid-name
        self.cc = None
        self.nc = self.text[0] if len(self.text) > 0 else "\0"
        self.nnc = self.text[1] if len(self.text) > 1 else "\0"
        # pylint: enable=invalid-name

        self.last_kind = None
        self.last_value = None

    def correct_tabs(self, tabwidth):
        assert isinstance(tabwidth, int) and tabwidth >= 2

        new_lines = []
        for line in self.context_line:
            tmp = ""
            for c in line:
                if c == "\t":
                    tmp += " " * (tabwidth - (len(tmp) % tabwidth))
                else:
                    tmp += c
            new_lines.append(tmp)
        self.context_line = new_lines
        self.text = "\n".join(new_lines) + "\n"

        self.cc = None
        self.nc = self.text[0] if len(self.text) > 0 else "\0"
        self.nnc = self.text[1] if len(self.text) > 1 else "\0"

    def next(self):
        self.lexpos += 1
        if self.cc == "\n":
            self.col_offset = self.lexpos
        self.cc = self.nc
        self.nc = self.nnc
        self.nnc = (self.text[self.lexpos + 2]
                    if len(self.text) > self.lexpos + 2
                    else "\0")

    def advance(self, n):
        assert isinstance(n, int) and n >= 0
        for _ in range(n):
            self.next()

    def match_re(self, regex):
        match = re.match("^" + regex,
                         self.text[self.lexpos:])
        if match is None:
            return None
        else:
            return match.group(0)

    def lex_error(self, message=None):
        mh.lex_error(Location(self.filename,
                              self.line,
                              self.lexpos - self.col_offset,
                              self.lexpos - self.col_offset,
                              self.context_line[self.line - 1]),
                     (message
                      if message
                      else "unexpected character %s" % repr(self.cc)))

    def token(self):
        # First we scan to the next non-whitespace token
        preceeding_ws = False
        while True:
            self.next()
            if self.cc in (" ", "\t"):
                preceeding_ws = True
            else:
                break

        t_start = self.lexpos
        col_start = t_start - self.col_offset

        # print("Begin lexing @ %u:%u <%s>" % (self.line,
        #                                      col_start,
        #                                      repr(self.cc)))

        if self.cc in ("%", "#"):
            # Comments go until the end of the line
            kind = "COMMENT"
            while self.nc not in ("\n", "\0"):
                self.next()

        elif self.cc == "\n":
            # Newlines are summarised into one token
            kind = "NEWLINE"
            while self.nc in ("\n", " ", "\t"):
                self.next()

        elif self.cc == ";":
            kind = "SEMICOLON"

        elif self.in_dir_command:
            kind = "DIRECTORY"
            while self.nc not in ("\n", "\0", "#", "%", ";"):
                self.next()

        elif self.cc == "." and self.nc == ".":
            # This is a continuation or the parent directory
            self.next()
            if self.nc == ".":
                kind = "CONTINUATION"
                self.next()

                # We now need to eat everything until and including
                # the next line
                while self.cc not in ("\n", "\0"):
                    self.next()

            else:
                self.lex_error("expected . to complete continuation token")

        elif self.cc.isalpha():
            # Could be an identifier or keyword
            kind = "IDENTIFIER"
            while self.nc.isalnum() or self.nc == "_":
                self.next()

        elif self.cc.isnumeric() or \
             self.cc == "." and self.nc.isnumeric():
            # Its some kind of number
            kind = "NUMBER"
            tmp = self.match_re(r"[0-9]*(\.[0-9]+)?([eE][+-]?[0-9]+)?")
            self.advance(len(tmp) - 1)

            # We need to make sure we now have something that isn't a
            # number to stop stupidity like 1.1.1
            if self.nc.isnumeric() or \
               self.nc == "." and self.nnc.isnumeric():
                self.lex_error()

        elif self.cc in ("<", ">", "=", "~"):
            # This is either a boolean relation, negation, or the
            # assignment
            if self.nc == "=":
                self.next()
                kind = "OPERATOR"
            elif self.cc == "=":
                kind = "ASSIGNMENT"
            else:
                kind = "OPERATOR"

        elif self.cc in ("+", "-", "*", "/", "^", "\\"):
            kind = "OPERATOR"

        elif self.cc in ("&", "|"):
            kind = "OPERATOR"
            if self.nc == self.cc:
                self.next()

        elif self.cc == "." and self.nc in ("*", "/", "\\", "^", "'"):
            kind = "OPERATOR"
            self.next()

        elif self.cc == "'":
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
            elif self.last_kind == "OPERATOR" and self.last_value == "'":
                kind = "OPERATOR"
            elif self.last_kind in ("BRA", "S_BRA", "C_BRA", "COMMA",
                                    "ASSIGNMENT", "OPERATOR", "SEMICOLON"):
                kind = "STRING"
            else:
                self.lex_error("unable to distinguish between string "
                               "and transpose operation")

            if kind == "STRING":
                while True:
                    self.next()
                    if self.cc == "'" and self.nc == "'":
                        self.next()
                    elif self.cc == "'":
                        break
                    elif self.cc in ("\n", "\0"):
                        self.lex_error()

        elif self.cc == '"':
            kind = "STRING"
            while True:
                self.next()
                if self.cc == '"' and self.nc == '"':
                    self.next()
                elif self.cc == '"':
                    break
                elif self.cc in ("\n", "\0"):
                    self.lex_error()

        elif self.cc == ",":
            kind = "COMMA"

        elif self.cc == ":":
            kind = "COLON"

        elif self.cc == "(":
            kind = "BRA"

        elif self.cc == ")":
            kind = "KET"

        elif self.cc == "{":
            kind = "C_BRA"

        elif self.cc == "}":
            kind = "C_KET"

        elif self.cc == "[":
            kind = "S_BRA"

        elif self.cc == "]":
            kind = "S_KET"

        elif self.cc == ".":
            kind = "SELECTION"

        elif self.cc == "@":
            kind = "AT"

        elif self.cc == "!":
            kind = "BANG"

        elif self.cc == "?":
            kind = "METACLASS"

        elif self.cc == "\0":
            return None

        else:
            self.lex_error()

        t_end = self.lexpos
        col_end = t_end - self.col_offset
        raw_text = self.text[t_start:t_end + 1]

        # print("Ended lexing @ %u:%u <%s>" % (self.line,
        #                                      self.col,
        #                                      repr(self.cc)))

        if kind == "IDENTIFIER" and raw_text in KEYWORDS:
            kind = "KEYWORD"

        token = MATLAB_Token(kind,
                             raw_text,
                             Location(self.filename,
                                      self.line,
                                      col_start,
                                      col_end,
                                      self.context_line[self.line - 1]),
                             self.first_in_line)
        self.first_in_line = False

        if kind == "NEWLINE":
            self.line += token.raw_text.count("\n")
            self.first_in_line = True
            self.in_dir_command = False
        elif kind == "CONTINUATION":
            self.line += 1
            self.first_in_line = True
            if self.in_dir_command:
                mh.error(token.location,
                         "cannot line-continue a cd command")
        elif kind == "IDENTIFIER" and token.first_in_line \
             and raw_text in ("cd", "mkdir", "rmdir"):
            self.in_dir_command = True

        self.last_kind = kind
        self.last_value = raw_text

        return token


class Token_Buffer(Token_Generator):
    def __init__(self, lexer):
        assert isinstance(lexer, MATLAB_Lexer)
        super().__init__(lexer.filename)

        self.pos = 0
        self.tokens = []
        while True:
            tok = lexer.token()
            if tok is None:
                break
            else:
                self.tokens.append(tok)

    def token(self):
        if self.pos < len(self.tokens):
            tok = self.tokens[self.pos]
            self.pos += 1
        else:
            tok = None

        return tok

    def reset(self):
        self.pos = 0

    def replay(self, fd):
        for n, token in enumerate(self.tokens):
            if n + 1 < len(self.tokens):
                next_token = self.tokens[n + 1]
            else:
                next_token = None
            if next_token and next_token.location.line == token.location.line:
                next_in_line = next_token
            else:
                next_in_line = None

            if token.first_in_line:
                fd.write(" " * token.location.col_start)

            if token.kind == "NEWLINE":
                amount = min(2, token.raw_text.count("\n"))
                if n + 1 == len(self.tokens):
                    # At the end of a file, we have at most one
                    # newline. This newline is inserted manually at
                    # the end
                    amount = 0
                fd.write("\n" * amount)
            elif token.kind == "CONTINUATION":
                fd.write(token.raw_text)
            else:
                fd.write(token.raw_text.rstrip())

            if next_in_line and next_in_line.kind != "NEWLINE":
                gap = (next_in_line.location.col_start -
                       (token.location.col_end + 1))
                # At most one space, unless we have a comment, then
                # it's ok for purposes of indentation
                #
                # This can mess up some nice alignment, so disabled for now
                # if next_in_line.kind not in ("COMMENT", "CONTINUATION"):
                #    gap = min(gap, 1)

                if (token.fix.get("ensure_trim_after", False) or
                    next_in_line.fix.get("ensure_trim_before", False)):
                    gap = 0
                elif (token.fix.get("ensure_ws_after", False) or
                      next_in_line.fix.get("ensure_ws_before", False)):
                    gap = max(gap, 1)

                fd.write(" " * gap)
        fd.write("\n")


def sanity_test():
    lexer = Token_Buffer(MATLAB_Lexer("tests/lexer/lexing_test.m"))

    while True:
        tok = lexer.token()
        if tok is None:
            break
        else:
            mh.info(tok.location, tok.kind)

    lexer = MATLAB_Lexer("tests/lexer/lexing_test_errors.m")

    try:
        while True:
            tok = lexer.token()
            if tok is None:
                break
    except Error:
        pass

    mh.print_summary_and_exit()


if __name__ == "__main__":
    sanity_test()
