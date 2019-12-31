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

from errors import Location, Error, Message_Handler, ICE
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
    "NUMBER",
    "CARRAY",          # 'foo' character array
    "STRING",          # "foo" string class literal
    "KEYWORD",
    "OPERATOR",
    "COMMA",
    "SEMICOLON",
    "COLON",
    "BRA", "KET",      # ( )
    "C_BRA", "C_KET",  # { }
    "M_BRA", "M_KET",  # [ ] for matrices
    "A_BRA", "A_KET",  # [ ] for assignment targets
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
    "BRA", "KET",      # ( )
    "C_BRA", "C_KET",  # { }
    "M_BRA", "M_KET",  # [ ] for matrices
    "A_BRA", "A_KET",  # [ ] for assignment targets
    "ASSIGNMENT",
    "SELECTION",
    "AT",
    "METACLASS"
])


class MATLAB_Token:
    def __init__(self,
                 kind,
                 raw_text,
                 location,
                 first_in_line,
                 first_in_statement,
                 anonymous = False,
                 contains_quotes = False):
        assert kind in TOKEN_KINDS
        assert isinstance(raw_text, str)
        assert isinstance(location, Location)
        assert isinstance(first_in_line, bool)
        assert isinstance(first_in_statement, bool)
        assert isinstance(anonymous, bool)
        assert isinstance(contains_quotes, bool)
        assert not contains_quotes or kind in ("STRING", "CARRAY")

        self.kind               = kind
        self.raw_text           = raw_text
        self.location           = location
        self.first_in_line      = first_in_line
        self.first_in_statement = first_in_statement
        self.anonymous          = anonymous
        self.contains_quotes    = contains_quotes

        # Not part of parsing, but some fix suggestions can be added
        self.fix = {}

    def value(self):
        if self.kind in TOKENS_WITH_IMPLICIT_VALUE:
            return None
        elif self.kind == "CONTINUATION":
            return self.raw_text[3:].strip()
        elif self.kind == "COMMENT":
            return self.raw_text[1:].strip()
        elif self.kind in ("CARRAY", "STRING"):
            if self.contains_quotes:
                return self.raw_text[1:-1]
            else:
                return self.raw_text
        elif self.kind == "BANG":
            return self.raw_text[1:]
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
    def __init__(self, mh, filename, encoding="utf-8"):
        super().__init__(filename)

        with open(filename, "r", encoding=encoding) as fd:
            self.text = fd.read()
        self.context_line = self.text.splitlines()

        self.mh = mh
        self.filename = filename
        self.lexpos = -1
        self.col_offset = 0
        self.line = 1

        self.first_in_line = True
        # Keep track if this would be the first token on a
        # typographical line (i.e. we do not take into account line
        # continuations). This is passed down to tokens themselves.

        self.first_in_statement = True
        # Flags tokens that are the first in a statement. This is true
        # if first_in_line is true and we did not have a continuation,
        # or after a comma or semicolon outside a matrix.

        self.bracket_stack = []
        # The lexer must keep track of brackets, since whitespace
        # works differently when in top-level matrix expressions. We
        # push the opening bracket tokens on this stack, and remove
        # them again when we encounter the relevant closing bracket.

        self.block_stack = []
        # The lexer must also keep track of any blocks, for example
        # classdef .. end, or properties .. end. Some blocks (such as
        # properties) should not be transformed to command-form.

        self.add_comma = False
        self.debug_comma = False
        # Sometimes (in matrices) we must add anonymous commas so that
        # the parser does not have to worry about whitespace. If the
        # debug flag is set to true we print some useful bits.

        self.in_lambda = False
        # If we encounter a lambda function (e.g. @(...) expr) then we
        # must *not* add a comma after the ) if it occurs in a matrix
        # or cell. This is a temporary override for add_comma.

        self.delay_list = []
        # See token() for a description.

        self.command_mode = False
        # If true, we completely change how we process input. Most
        # things will be returned as strings, except for line
        # continuations. Comments and newlines end command form.

        self.comment_char = frozenset("%")
        # Characters that start a line comment. MATLAB only uses %,
        # and Octave uses either.
        #
        # TODO: This should be configurable (see #44).

        self.in_special_section = False
        # Some keywords (properties, attributes, etc.) introduce a
        # special section, in which the command_mode is never
        # activated. This section ends with the first 'end' keyword is
        # encountered.

        self.config_file_mode = False
        # We abuse this lexer to parse our config files. If this is
        # set, we don't do command_mode at all, because quite frankly
        # this concept is idiotic.

        self.octave_mode = False
        # If set to true, also deal with Octave's extensions to
        # MATLAB.
        #
        # Note that this is highly incomplete right now.

        self.block_comment = 0
        # We're in a block comment and are ignore almost everything
        # (except a closing block comment). This is a number because
        # block comments could be nested, and we use this to keep
        # track of the level.

        # pylint: disable=invalid-name
        self.cc = None
        self.nc = self.text[0] if len(self.text) > 0 else "\0"
        self.nnc = self.text[1] if len(self.text) > 1 else "\0"
        self.nnnc = self.text[2] if len(self.text) > 2 else "\0"
        # pylint: enable=invalid-name

        self.last_kind = None
        self.last_value = None

    def set_octave_mode(self):
        self.octave_mode = True
        self.comment_char = frozenset("%#")

    def set_config_file_mode(self):
        self.config_file_mode = True
        self.comment_char = frozenset("#")

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
        self.nnc = self.nnnc
        self.nnnc = (self.text[self.lexpos + 3]
                     if len(self.text) > self.lexpos + 3
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
        self.mh.lex_error(Location(self.filename,
                                   self.line,
                                   self.lexpos - self.col_offset,
                                   self.lexpos - self.col_offset,
                                   self.context_line[self.line - 1]),
                          (message
                           if message
                           else "unexpected character %s" % repr(self.cc)))

    def contains_block_open(self, string):
        for c in self.comment_char:
            if c + "{" in string:
                return True
        return False

    def contains_block_close(self, string):
        for c in self.comment_char:
            if c + "}" in string:
                return True
        return False

    def __token(self):
        # If we've been instructed to add an anonymous comma, we do
        # that and nothing else.
        if self.add_comma:
            self.add_comma = False
            fake_line = self.context_line[self.line - 1]
            fake_col = self.lexpos - self.col_offset + 1
            fake_line = fake_line[:fake_col] + "<anon,>" + fake_line[fake_col:]
            token = MATLAB_Token("COMMA",
                                 ",",
                                 Location(self.filename,
                                          self.line,
                                          fake_col,
                                          fake_col + 6,
                                          fake_line),
                                 False,
                                 False,
                                 anonymous = True)
            self.last_kind = "COMMA"
            self.last_value = ","
            return token

        # First we scan to the next non-whitespace character, unless
        # we're in block comment mode
        preceeding_ws = False
        while not self.block_comment:
            self.next()
            if self.cc in (" ", "\t"):
                preceeding_ws = True
            else:
                break

        if self.block_comment:
            self.next()

        t_start = self.lexpos
        col_start = t_start - self.col_offset
        contains_quotes = False

        # print("Begin lexing @ %u:%u <%s>" % (self.line,
        #                                      col_start,
        #                                      repr(self.cc)))

        if self.cc == "\0":
            return None

        elif self.block_comment:
            if self.cc == "\n":
                kind = "NEWLINE"
            else:
                kind = "COMMENT"
                while self.nc not in ("\n", "\0"):
                    self.next()

        elif self.command_mode:
            # Lexing in command mode
            if self.cc in self.comment_char:
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

            elif self.cc == ",":
                kind = "COMMA"

            elif self.cc == "'":
                kind = "CARRAY"
                contains_quotes = True
                while True:
                    self.next()
                    if self.cc == "'" and self.nc == "'":
                        self.next()
                    elif self.cc == "'":
                        break
                    elif self.cc in ("\n", "\0"):
                        self.lex_error()

            elif self.cc == "." and \
                 self.nc == "." and \
                 self.nnc == ".":
                kind = "CONTINUATION"
                # We now need to eat everything until and including
                # the next line
                while self.cc not in ("\n", "\0"):
                    self.next()

            else:
                # Everything else in command form is converted into a
                # string.
                kind = "CARRAY"
                while self.nc not in (" ", "\t", "\n", "\0", ",", ";"):
                    # We just need to make sure to not eat line
                    # continuatins by accident
                    if self.nc == "." and \
                       self.nnc == "." and \
                       self.nnnc == ".":
                        break

                    # We also need to make sure not to eat comments
                    if self.nc in self.comment_char:
                        break

                    self.next()

        else:
            # Ordinary lexing

            if self.cc in self.comment_char:
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

            elif self.cc == "." and self.nc == ".":
                # This is a continuation
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
                tmp = self.match_re(
                    r"([0-9]+(\.[0-9]*)?([eE][+-]?[0-9]+)?[iIjJ]?)|"
                    r"(\.[0-9]+([eE][+-]?[0-9]+)?[iIjJ]?)")
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
                    kind = "CARRAY"
                    contains_quotes = True
                elif self.last_kind in ("IDENTIFIER", "NUMBER", "CARRAY",
                                        "KET", "M_KET", "C_KET"):
                    kind = "OPERATOR"
                elif self.last_kind == "OPERATOR" and self.last_value == "'":
                    kind = "OPERATOR"
                elif self.last_kind in ("BRA", "M_BRA", "C_BRA", "COMMA",
                                        "ASSIGNMENT", "OPERATOR", "SEMICOLON"):
                    kind = "CARRAY"
                    contains_quotes = True
                else:
                    self.lex_error("unable to distinguish between string "
                                   "and transpose operation")

                if kind == "CARRAY":
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
                contains_quotes = True
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
                # I have decided to not do what is described in section 7
                # of the 1999 technical report, since it makes it very
                # hard to deal with stuff like [a.('foo')] = 10. The
                # lookahead for the = would be bordering on impossible if
                # we need to ignore = inside strings.
                #
                # Instead we're going to do this as a post-processing step
                # that delays returning from the lexer until we encounter
                # an = after the coressponding closing bracket, or not.
                kind = "M_BRA"

            elif self.cc == "]":
                kind = "M_KET"

            elif self.cc == ".":
                kind = "SELECTION"

            elif self.cc == "@":
                kind = "AT"

            elif self.cc == "!":
                # Shell escapes go up to the end of the line
                while self.nc not in ("\n", "\0"):
                    self.next()
                kind = "BANG"

            elif self.cc == "?":
                kind = "METACLASS"

            else:
                self.lex_error()

        t_end = self.lexpos
        col_end = t_end - self.col_offset
        raw_text = self.text[t_start:t_end + 1]

        # print("Ended lexing @ %u:%u <%s>" % (self.line,
        #                                      col_end,
        #                                      repr(self.cc)))

        # Classify keywords, except after selections. That way we
        # permit structure fields with names like "function".
        if kind == "IDENTIFIER" and \
           raw_text in KEYWORDS and \
           self.last_kind != "SELECTION":
            kind = "KEYWORD"

        # Keep track of blocks, and special sections where
        # command-form is disabled.
        if not self.bracket_stack:
            if kind == "KEYWORD" and \
               raw_text in ("classdef", "function",
                            "for", "if", "parfor", "switch",
                            "try", "while", "spmd"):
                self.block_stack.append(raw_text)

            if self.block_stack and kind == "IDENTIFIER":
                extra_kw = set()
                if self.last_kind == "SELECTION":
                    # Like with other keywords above, if the
                    # preceeding token is a field selection we never
                    # produce keywords.
                    pass
                elif self.block_stack[-1] == "classdef":
                    # Directly inside a classdef, we have 4 extra
                    # keywords
                    extra_kw = {"properties", "enumeration",
                                "events",     "methods"}
                elif self.block_stack[-1] in ("properties",
                                              "enumeration",
                                              "events"):
                    # In three of the four class blocks, these
                    # keywords persist
                    extra_kw = {"properties", "enumeration",
                                "events",     "methods"}
                elif self.block_stack[-1] == "function":
                    # Inside functions we add the arguments block as
                    # an extra keyword
                    extra_kw = {"arguments"}

                if raw_text in extra_kw:
                    kind = "KEYWORD"
                    self.block_stack.append(raw_text)
                    if raw_text in ("properties", "events",
                                    "enumeration", "arguments"):
                        self.in_special_section = True

            elif kind == "KEYWORD" and raw_text == "end":
                if self.block_stack:
                    self.block_stack.pop()
                self.in_special_section = False
                # TODO: Silent error if we can't match blocks? Or
                # complain loudly?

        if self.line - 1 < len(self.context_line):
            ctx_line = self.context_line[self.line - 1]
        else:
            raise ICE("line is larger than the length of the file %s" %
                      self.filename)

        token = MATLAB_Token(kind,
                             raw_text,
                             Location(self.filename,
                                      self.line,
                                      col_start,
                                      col_end,
                                      ctx_line),
                             self.first_in_line,
                             self.first_in_statement,
                             contains_quotes = contains_quotes)
        self.first_in_line = False
        self.first_in_statement = False

        if kind == "BRA" and self.last_kind == "AT":
            self.in_lambda = True

        if kind == "NEWLINE":
            self.line += token.raw_text.count("\n")
            self.first_in_line = True
        elif kind == "CONTINUATION":
            self.line += 1
            self.first_in_line = True

        # Detect if we should enter command form. If the next
        # character is not a space, it's never a command.
        if not self.config_file_mode and \
           not self.in_special_section and \
           token.first_in_statement and \
           token.kind == "IDENTIFIER" and \
           self.nc in (" ", "\t"):
            # We need to scan ahead to the next non-space character
            mode = "search_ws"
            for n, c in enumerate(self.text[self.lexpos + 1:],
                                  self.lexpos + 1):
                if mode == "search_ws":
                    if c == "\n":
                        # We found a newline, so we had a identifier
                        # followed by trailing whitespace. No need to
                        # enter command form.
                        break
                    elif c in (" ", "\t"):
                        # Skip spaces
                        pass
                    elif c == "(":
                        # Open bracket is always a function call
                        break
                    elif c in r"+-*/\^'@?:":
                        # Single-character operators
                        mode = "found_op"
                    elif c in r"<>&|~.=":
                        # Single or multi-char operators. We need to
                        # lookahead by 1 here.
                        if n + 1 < len(self.text):
                            # pylint: disable=invalid-name
                            nc = self.text[n + 1]
                            # pylint: enable=invalid-name
                        else:
                            break

                        if c == "<" and nc == "=":
                            mode = "skip_one"
                        elif c == ">" and nc == "=":
                            mode = "skip_one"
                        elif c == "&" and nc == "&":
                            mode = "skip_one"
                        elif c == "|" and nc == "|":
                            mode = "skip_one"
                        elif c == "~" and nc == "=":
                            mode = "skip_one"
                        elif c == "." and nc in r"*/\&'?":
                            mode = "skip_one"
                        elif c == "=" and nc == "=":
                            mode = "skip_one"
                        elif c == "=":
                            # Assignment, so never a command
                            break
                        else:
                            mode = "found_op"
                    else:
                        # Anything else indicates a command
                        self.command_mode = True
                        break

                elif mode == "skip_one":
                    mode = "found_op"

                elif mode == "found_op":
                    # We found an operator after a whitespace. Now we
                    # need to check if this character is also a space,
                    # in which case we do not have a
                    # command. Otherwise, it's a command
                    if c in (" ", "\t"):
                        break
                    else:
                        self.command_mode = True
                        break

                else:
                    raise ICE("logic error")

        # Detect new statements. Note that this flags comments as
        # well, but that is fine.
        if not self.bracket_stack:
            if kind in ("NEWLINE", "COMMA", "SEMICOLON"):
                self.first_in_statement = True
                self.command_mode = False

        # Detect block comment starts (and questionable block comments)
        if token.kind == "COMMENT" and \
           ((self.block_comment == 0 and
             token.raw_text[1:2] == "{") or
            (self.block_comment > 0 and
             self.contains_block_open(token.raw_text))):

            if not token.first_in_line and self.block_comment == 0:
                self.mh.warning(token.location,
                                "ignored block comment: it must not be"
                                " preceded by program text")
            elif token.value().strip() != "{" and self.block_comment == 0:
                self.mh.warning(token.location,
                                "ignored block comment: no text must appear"
                                " after the {")
            elif token.raw_text.strip() not in ["%s{" % c
                                                for c in self.comment_char]:
                self.mh.warning(token.location,
                                "ignored block comment: no text must appear"
                                " around the block comment marker")
            else:
                self.block_comment += 1

        elif self.block_comment and token.kind == "COMMENT":
            for c in self.comment_char:
                marker = c + "}"
                if marker in token.raw_text:
                    if token.raw_text.strip() == marker:
                        self.block_comment -= 1
                    else:
                        self.mh.warning(token.location,
                                        "ignored block comment end: no text"
                                        " must appear around the block comment"
                                        " marker %s" % marker)

        self.last_kind = kind
        self.last_value = raw_text

        if token.kind in ("BRA", "M_BRA", "C_BRA"):
            self.bracket_stack.append(token)
        elif token.kind in ("KET", "M_KET", "C_KET"):
            if self.bracket_stack:
                matching_bracket = self.bracket_stack.pop()
                if (token.kind == "KET" and
                    matching_bracket.kind != "BRA") or \
                   (token.kind == "M_KET" and
                    matching_bracket.kind != "M_BRA") or \
                   (token.kind == "C_KET" and
                    matching_bracket.kind != "C_BRA"):
                    self.mh.lex_error(token.location,
                                      "mismatched brackets %s ... %s" %
                                      (matching_bracket.raw_text,
                                       token.raw_text))
            else:
                # Raise a non-fatal lex error (so that the style
                # checker can continue; the parser will throw up soon
                # anyway).
                self.mh.lex_error(token.location,
                                  "unmatched %s" % token.raw_text,
                                  False)

        ######################################################################
        # Add commas if we're in matrices or cells

        # Determine if whitespace is currently significant (i.e. we're
        # in a matrix).
        ws_is_significant = (self.bracket_stack and
                             self.bracket_stack[-1].kind in ("M_BRA",
                                                             "C_BRA") and
                             self.bracket_stack[-1] != token)

        # Determine if there is whitespace after the current token
        ws_follows = self.nc in (" ", "\t")

        # Determine what the next two characters that follows this
        # token, after skipping whitespace
        skip_cont = False
        next_non_ws = None
        after_next_non_ws = None
        for n, c in enumerate(self.text[self.lexpos + 1:],
                              self.lexpos + 1):
            if skip_cont and c == "\n":
                skip_cont = False
            elif skip_cont:
                pass
            elif c in (" ", "\t") and next_non_ws is None:
                pass
            elif self.text[n:n + 3] == "..." and next_non_ws is None:
                skip_cont = True
                # Also, continuations count like whitespace for the
                # purposes of adding commas.
                ws_follows = True
            elif next_non_ws is None:
                next_non_ws = c
            else:
                after_next_non_ws = c
                break

        # Commas can only meaningfully appear after a set number of
        # tokens. token_relevant is set to true if have such a token.
        # TODO: This doesn't deal with continuations yet, and it
        # probably won't work correctly.
        token_relevant = (token.kind in ("IDENTIFIER",
                                         "NUMBER",
                                         "CARRAY",
                                         "STRING",
                                         "KET",
                                         "M_KET",
                                         "C_KET") or
                          (token.kind == "KEYWORD" and
                           token.value() == "end") or
                          (token.kind == "OPERATOR" and
                           token.value() in ("'", ".'")))

        # Look at the next 2 characters that are not whitespace. Lets
        # rule out some cases
        if next_non_ws and after_next_non_ws:
            if next_non_ws == "." and after_next_non_ws.isdigit():
                pass
            elif next_non_ws in r"*/\^<>&|=.:!":
                token_relevant = False
            elif next_non_ws == "~" and after_next_non_ws == "=":
                token_relevant = False

        if ws_is_significant and ws_follows and next_non_ws and token_relevant:
            # There is whitespace after our token, and the next thing
            # looks like it could maybe mean there is a comma here.
            #
            # The next thing could be
            #   NEWLINE      (nothing to do)
            #   CONTINUATION (ignore for now)
            #   COMMENT      (nothing to do)
            #   IDENTIFIER   (entails comma)
            #   NUMBER       (entails comma)
            #   CARRAY/'     (carray = comma, transpose = no comma)
            #   STRING       (entails comma)
            #   KEYWORD      (syntax error)
            #   OPERATOR     ruled out, except for:
            #     unary +-   ?
            #     '          (impossible, since we have ws)
            #     ~          ?
            #   COMMA        (nothing to do)
            #   COLON        ?
            #   ( { [        (entails comma)
            #   ASSIGNMENT   (syntax error)
            #   SELECTION    (ruled out)
            #   AT           (entails comma)
            #   BANG         (syntax error)
            #   METACLASS    (entails comma)

            if next_non_ws in (",", ";", "\n"):
                # COMMA
                # NEWLINE
                # SEMICOLON
                pass
            elif next_non_ws in self.comment_char:
                # COMMENT
                pass
            elif next_non_ws.isalnum():
                # IDENTIFIER, NUMBER
                self.add_comma = True
            elif next_non_ws in ("'", '"'):
                # CARRAY, STRING
                self.add_comma = True
            elif next_non_ws in "([{":
                # BRA, M_BRA, C_BRA
                self.add_comma = True
            elif next_non_ws in "@?":
                # AT, METACLASS
                self.add_comma = True
            elif next_non_ws == ".":
                # .5 (we've ruled out everything else with .)
                self.add_comma = True
            elif next_non_ws in "-+~":
                if after_next_non_ws in ("+", "-", "("):
                    self.add_comma = True
                elif after_next_non_ws.isalnum():
                    # +6...
                    self.add_comma = True

        if self.in_lambda and token.kind == "KET":
            self.add_comma = False
            self.in_lambda = False

        return token

    def token(self):
        # To deal with assignment, it is sometimes necessary to delay
        # returning tokens until we know if we get "] =" or not.

        if self.delay_list:
            tok = self.delay_list.pop(0)
            return tok

        tok = self.__token()
        if tok is None:
            return None

        if len(self.bracket_stack) > 1 or tok.kind != "M_BRA":
            # We're in a nested context, or this is not a [. Just
            # return the token.
            return tok

        open_bracket = tok
        if open_bracket.kind != "M_BRA":
            raise ICE("supposed open bracket is %s instead" %
                      open_bracket.kind)

        # We have a top-level [. So now we squirrel away tokens until
        # we get to the matching closing bracket.
        self.delay_list = [tok]
        while self.bracket_stack:
            tok = self.__token()
            self.delay_list.append(tok)
            if tok is None:
                break

        close_bracket = self.delay_list[-1]
        if close_bracket is not None and close_bracket.kind != "M_KET":
            raise ICE("supposed close bracket is %s instead" %
                      close_bracket.kind)

        # Now we add more until we hit an assignment or not a
        # continuation
        while close_bracket:
            tok = self.__token()
            self.delay_list.append(tok)
            if tok is None:
                break
            elif tok.kind == "CONTINUATION":
                continue
            else:
                break

        # Now we check if we have an =
        tok = self.delay_list[-1]
        if tok and tok.kind == "ASSIGNMENT":
            open_bracket.kind = "A_BRA"
            close_bracket.kind = "A_KET"

        # Finally, start by returning the first token
        tok = self.delay_list.pop(0)
        return tok


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

    # def extended_iterate(self):
    #     self.reset()
    #     rv = {
    #         "id"            : self.pos,
    #         "next_token"    : None,
    #         "prev_token"    : None,
    #         "next_in_line"  : None,
    #         "prev_in_line"  : None,
    #         "ws_before"     : None,
    #         "ws_after"      : None,
    #         "first_in_line" : True,
    #         "last_in_line"  : None,
    #     }
    #     tok = self.token
    #     rv["next_token"] = self.token()

    #     def set_last_in_line():
    #         rv["last_in_line"] = (rv["next_token"] and
    #                               rv["next_token"].kind == "NEWLINE")

    #     def advance():
    #         rv["id"] = self.pos
    #         rv["prev_token"] = tok
    #         tok = rv["next_token"]
    #         rv["next_token"] = self.token()

    #     def set_neighbours():
    #         if not tok or tok.first_in_line:
    #             rv["prev_in_line"] = None
    #             rv["ws_before"] = None
    #         else:
    #             rv["prev_in_line"] = rv["prev_token"]
    #             rv["ws_before"] = (tok.location.col_start -
    #                                rv["prev_in_line"].location.col_end) - 1

    #         if not rv["next_token"] or rv["next_token"].kind == "NEWLINE":
    #             rv["next_in_line"] = None
    #             rv["ws_after"] = None
    #         else:
    #             rv["next_in_line"] = rv["next_token"]
    #             rv["ws_after"] = (rv["next_in_line"].location.col_start -
    #                               tok.location.col_end) - 1

    #     set_last_in_line()

    def replay(self, fd):
        real_tokens = [t for t in self.tokens if not t.anonymous]

        for n, token in enumerate(real_tokens):
            if n + 1 < len(real_tokens):
                next_token = real_tokens[n + 1]
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
                if n + 1 == len(real_tokens):
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


def sanity_test(mh, filename):
    try:
        mh.register_file(filename)
        lexer = MATLAB_Lexer(mh, filename)
        lexer.debug_comma = True
        while True:
            tok = lexer.token()
            if tok is None:
                break
            else:
                if tok.first_in_statement or tok.first_in_line:
                    txt = "[%s%s] %s" % (
                        "S" if tok.first_in_statement else " ",
                        "L" if tok.first_in_line else " ",
                        tok.kind)
                else:
                    txt = tok.kind
                mh.info(tok.location, txt)
        print("%s: lexed OK" % filename)
    except Error:
        print("%s: lexed with errors" % filename)
    except ICE as internal_compiler_error:
        print("%s: ICE: %s" % (filename, internal_compiler_error.reason))


def lexer_test_main():
    from argparse import ArgumentParser
    ap = ArgumentParser()
    ap.add_argument("file")
    options = ap.parse_args()

    mh = Message_Handler()
    mh.sort_messages = False
    mh.colour = True

    sanity_test(mh, options.file)

    mh.summary_and_exit()


if __name__ == "__main__":
    lexer_test_main()
