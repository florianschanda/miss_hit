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

# This is a stylechecker for (mostly) whitespace issues. It can
# rewrite the code to fix most of them.

import sys
import os
import argparse
import re
import traceback
import textwrap

from abc import ABCMeta, abstractmethod

from m_language_builtins import BUILTIN_FUNCTIONS
from m_lexer import MATLAB_Lexer, Token_Buffer
from errors import Location, Error, ICE, mh
import config

# pylint: disable=wildcard-import,unused-wildcard-import
from m_ast import *
# pylint: enable=wildcard-import,unused-wildcard-import

GITHUB_ISSUES = "https://github.com/florianschanda/miss_hit/issues"

COPYRIGHT_REGEX = r"(\(c\) )?Copyright (\d\d\d\d-)?\d\d\d\d *(?P<org>.*)"


class Mini_Parser:
    def __init__(self, tbuf, idx):
        assert isinstance(tbuf, Token_Buffer)
        assert isinstance(idx, int) and 0 <= idx < len(tbuf.tokens)

        self.tbuf = tbuf
        self.c_idx = None
        self.n_idx = idx

        # pylint: disable=invalid-name
        self.ct = None
        self.nt = self.get_token(idx)
        # pylint: enable=invalid-name

        self.filename = self.nt.location.filename

    def get_token(self, n):
        if n < len(self.tbuf.tokens):
            return self.tbuf.tokens[n]
        else:
            return None

    def next(self):
        self.c_idx = self.n_idx
        self.ct = self.nt

        self.n_idx += 1
        self.nt = self.get_token(self.n_idx)

        while self.nt:
            # Skip comments and continuations
            while self.nt and self.nt.kind in ("COMMENT", "CONTINUATION"):
                self.n_idx += 1
                self.nt = self.get_token(self.n_idx)

            # Join new-lines
            if (self.nt and
                self.ct and
                self.nt.kind == "NEWLINE" and
                self.ct.kind == "NEWLINE"):
                self.n_idx += 1
                self.nt = self.get_token(self.n_idx)
            else:
                break

    def match(self, kind, value=None):
        self.next()
        if self.ct is None:
            mh.error(Location(self.filename),
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

    def parse_identifier(self, in_reference=False):
        if self.peek("OPERATOR", "~") and in_reference:
            self.match("OPERATOR")
            return Identifier(self.ct)
        else:
            self.match("IDENTIFIER")
            return Identifier(self.ct)

    def parse_selection(self, in_reference=False):
        rv = self.parse_identifier(in_reference)

        if rv.t_ident.value() == "~":
            return rv

        while self.peek("SELECTION"):
            self.match("SELECTION")
            dot = self.ct
            field = self.parse_identifier()
            rv = Selection(dot, rv, field)

        return rv

    def parse_function_declaration(self):
        self.match("KEYWORD", "function")

        # Parse returns. Either 'x' or a list '[x, y]'
        returns = []
        if self.peek("A_BRA"):
            out_brackets = True
            self.match("A_BRA")
            if self.peek("A_KET"):
                self.match("A_KET")
            else:
                while True:
                    returns.append(self.parse_selection(in_reference=True))
                    if self.peek("COMMA"):
                        self.match("COMMA")
                    else:
                        break
                self.match("A_KET")
        else:
            out_brackets = False
            returns.append(self.parse_selection())

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
            function_name = self.parse_selection()

        # Currently disabled. It generates a lot of alarms for classes.
        # if isinstance(function_name, Identifier):
        #     if function_name.t_ident.value() in BUILTIN_FUNCTIONS:
        #         mh.warning(function_name.t_ident.location,
        #                    "redefinition of builtin function is a"
        #                    " very naughty thing to do")

        inputs = []
        if self.peek("BRA"):
            self.match("BRA")
            if self.peek("KET"):
                self.match("KET")
            else:
                while True:
                    self.parse_identifier(in_reference=True)
                    inputs.append(self.ct.value())
                    if self.peek("COMMA"):
                        self.match("COMMA")
                    else:
                        break
                self.match("KET")

        if self.peek("SEMICOLON"):
            self.match("SEMICOLON")

        self.match("NEWLINE")

##############################################################################


class Style_Rule(metaclass=ABCMeta):
    def __init__(self, name, autofix):
        assert isinstance(name, str)
        assert isinstance(autofix, bool)
        self.name = name
        self.autofix = autofix
        self.mandatory = False


class Style_Rule_File(Style_Rule):
    def __init__(self, name):
        super().__init__(name, False)

    @abstractmethod
    def apply(self, cfg, filename, lines):
        pass


class Style_Rule_Line(Style_Rule):
    @abstractmethod
    def apply(self, cfg, filename, line_no, line):
        pass


class Rule_File_Length(Style_Rule_File):
    """Maximum file length

    This is configurable with `file_length`. It is a good idea to keep
    the length of your files under some limit since it forces your
    project into avoiding the worst spaghetti code.

    """

    parameters = {
        "file_length": {
            "type"    : int,
            "metavar" : "N",
            "help"    : "Maximum lines in a file, 1000 by default.",
        }
    }

    defaults = {
        "file_length" : 1000,
    }

    def __init__(self):
        super().__init__("file_length")

    def apply(self, cfg, filename, lines):
        if len(lines) > cfg["file_length"]:
            mh.style_issue(Location(filename,
                                    len(lines)),
                           "file exceeds %u lines" % cfg["file_length"],
                           self.autofix)


class Rule_File_EOF_Lines(Style_Rule_File):
    """Trailing newlines at end of file

    This mandatory rule makes sure there is a single trailing newline
    at the end of a file.

    """

    def __init__(self):
        super().__init__("eof_newlines")
        self.mandatory = True
        self.autofix = True

    def apply(self, cfg, filename, lines):
        if len(lines) >= 2 and lines[-1] == "":
            mh.style_issue(Location(filename,
                                    len(lines)),
                           "trailing blank lines at end of file",
                           self.autofix)


class Rule_Line_Length(Style_Rule_Line):
    """Max characters per line

    This is configurable with `line_length`, default is 80. It is a
    good idea for readability to avoid overly long lines. This can help
    you avoid extreme levels of nesting and avoids having to scroll
    around.

    """

    parameters = {
        "line_length": {
            "type"    : int,
            "metavar" : "N",
            "help"    : "Maximum characters per line, 80 by default.",
        }
    }

    defaults = {
        "line_length" : 80,
    }

    def __init__(self):
        super().__init__("line_length", False)

    def apply(self, cfg, filename, line_no, line):
        if len(line) > cfg["line_length"] + 1:
            mh.style_issue(Location(filename,
                                    line_no,
                                    cfg["line_length"] + 1,
                                    len(line),
                                    line),
                           "line exceeds %u characters" % cfg["line_length"],
                           self.autofix)


class Rule_Line_Blank_Lines(Style_Rule_Line):
    """Consecutive blank lines

    This rule allows a maximum of one blank line to separate code blocks.
    Comments are not considered blank lines.

    """

    def __init__(self):
        super().__init__("consecutive_blanks", True)
        self.mandatory = True
        self.is_blank = False

    def apply(self, cfg, filename, line_no, line):
        if len(line.strip()):
            self.is_blank = False
        elif self.is_blank:
            mh.style_issue(Location(filename,
                                    line_no),
                           "more than one consecutive blank line",
                           self.autofix)
        else:
            self.is_blank = True


class Rule_Line_Tabs(Style_Rule_Line):
    """Use of tab

    This rule enforces the absence of the tabulation character
    *everywhere*. When auto-fixing, a tab-width of 4 is used by default,
    but this can be configured with the options `tab_width`.

    Note that the fix replaces the tab everywhere, including in strings
    literals. This means
    ```
    "a<tab>b"
       "a<tab>b"
    ```
    might be fixed to
    ```
    "a        b"
       "a     b"
    ```

    Which may or may not what you had intended originally. I am not sure
    if this is a bug or a feature, but either way it would be *painful* to
    change so I am going to leave this as is.

    """

    parameters = {
        "tab_width": {
            "type"    : int,
            "metavar" : "N",
            "help"    : "Tab-width, by default 4.",
        }
    }

    defaults = {
        "tab_width" : 4,
    }

    def __init__(self):
        super().__init__("tabs", True)
        self.mandatory = True

    def apply(self, cfg, filename, line_no, line):
        if "\t" in line:
            mh.style_issue(Location(filename,
                                    line_no,
                                    line.index("\t"),
                                    line.index("\t"),
                                    line),
                           "tab is not allowed",
                           self.autofix)


class Rule_Line_Trailing_Whitesapce(Style_Rule_Line):
    """Trailing whitespace

    This rule enforces that there is no trailing whitespace in your files.
    You *really* want to do this, even if the MATLAB default editor makes
    this really hard. The reason is that it minimises conflicts when using
    modern version control systems.

    """

    def __init__(self):
        super().__init__("trailing_whitespace", True)
        self.mandatory = True

    def apply(self, cfg, filename, line_no, line):
        if line.endswith(" "):
            if len(line.strip()) == 0:
                mh.style_issue(Location(filename,
                                        line_no),
                               "whitespace on blank line",
                               self.autofix)
            else:
                mh.style_issue(Location(filename,
                                        line_no,
                                        len(line.rstrip()),
                                        len(line),
                                        line),
                               "trailing whitespace",
                               self.autofix)


def get_rules():
    rules = {
        "on_file" : [],
        "on_line" : [],
        "on_token" : [],
    }

    def rec(root):
        is_leaf = True
        for subclass in root.__subclasses__():
            rec(subclass)
            is_leaf = False

        if is_leaf:
            if issubclass(root, Style_Rule_File):
                rules["on_file"].append(root)
            elif issubclass(root, Style_Rule_Line):
                rules["on_line"].append(root)
            else:
                raise ICE("Unable to categorize %s with base %s" %
                          (root.__name__,
                           " and ".join(b.__name__
                                        for b in root.__bases__)))

    rec(Style_Rule)
    return rules


def build_library(cfg, rules):
    lib = {
        "on_file" : [],
        "on_line" : [],
        "on_token" : []
    }

    for kind in rules:
        for rule in rules[kind]:
            inst = rule()
            if inst.mandatory or config.active(cfg, inst.name):
                lib[kind].append(inst)

    return lib


def build_default_config(rule_set):
    cfg = {}

    for kind in rule_set:
        for rule in rule_set[kind]:
            cfg.update(getattr(rule, "defaults", {}))

    return cfg


##############################################################################


WORDS_WITH_WS = frozenset([
    "case",
    "catch",
    "classdef",
    "elseif",
    "for",
    "function",
    "global",
    "if",
    "parfor",
    "persistent",
    "switch",
    "while",

    # These are not keywords, but we treat them like it.
    "properties",
    "methods",
    "events",
])


def stage_3_analysis(cfg, tbuf):
    assert isinstance(tbuf, Token_Buffer)

    in_copyright_notice = config.active(cfg, "copyright_notice")
    company_copyright_found = False
    generic_copyright_found = False
    copyright_token = None
    copyright_notice = []

    last_newline = 0

    for n, token in enumerate(tbuf.tokens):
        if n - 1 >= 0:
            prev_token = tbuf.tokens[n - 1]
        else:
            prev_token = None

        if n + 1 < len(tbuf.tokens):
            next_token = tbuf.tokens[n + 1]
        else:
            next_token = None

        if (prev_token and
            prev_token.location.line == token.location.line):
            prev_in_line = prev_token
            ws_before = (token.location.col_start -
                         prev_in_line.location.col_end) - 1

        else:
            prev_in_line = None
            ws_before = None

        if token.kind == "NEWLINE":
            last_newline = n

        if (next_token and
            next_token.location.line == token.location.line):
            if next_token.kind == "NEWLINE":
                next_in_line = None
                ws_after = None
            else:
                next_in_line = next_token
                ws_after = (next_in_line.location.col_start -
                            token.location.col_end) - 1
        else:
            next_in_line = None
            ws_after = None

        if token.kind in ("NEWLINE", "COMMENT", "CONTINUATION"):
            last_code_in_line = False
        elif next_in_line is None:
            last_code_in_line = True
        elif next_in_line.kind in ("NEWLINE", "COMMENT"):
            last_code_in_line = True
        else:
            last_code_in_line = False

        # Recognize justifications
        if token.kind in ("COMMENT", "CONTINUATION"):
            if "mh:ignore_style" in token.value():
                mh.register_justification(token)

        # Corresponds to the old CodeChecker CopyrightCheck rule
        if in_copyright_notice:
            if token.kind == "COMMENT":
                match = re.search(COPYRIGHT_REGEX, token.value())
                if match:
                    # We have a sane copyright string
                    copyright_token = token
                    generic_copyright_found = True
                    if match.group("org").strip() in cfg["copyright_entity"]:
                        company_copyright_found = True

                elif copyright_token is None:
                    # We might find something that could look like a
                    # copyright, but is not quite right
                    for org in cfg["copyright_entity"]:
                        if org.lower() in token.value().lower():
                            copyright_token = token
                            break
                    for substr in ("(c)", "copyright"):
                        if substr in token.value().lower():
                            copyright_token = token
                            break

                copyright_notice.append(token.value())

            else:
                # Once we get a non-comment token, the header has
                # ended. We then emit messages if we could not find
                # anything.
                in_copyright_notice = False

                if len(copyright_notice) == 0:
                    mh.style_issue(token.location,
                                   "file does not appear to contain any"
                                   " copyright header")
                elif company_copyright_found:
                    # Everything is fine
                    pass
                elif generic_copyright_found:
                    # If we have something basic, we only raise an
                    # issue if we're supposed to have something
                    # specific.
                    if cfg["copyright_entity"]:
                        mh.style_issue(copyright_token.location,
                                       "Copyright does not mention one of %s" %
                                       (" or ".join(cfg["copyright_entity"])))
                elif copyright_token:
                    # We found something that might be a copyright,
                    # but is not in a sane format
                    mh.style_issue(copyright_token.location,
                                   "Copyright notice not in right format")
                else:
                    # We found nothing
                    mh.style_issue(token.location,
                                   "No copyright notice found in header")

        # Corresponds to the old CodeChecker CommaLineEndings and
        # CommaWhitespace rules
        if token.kind == "COMMA":
            if config.active(cfg, "whitespace_comma"):
                token.fix["ensure_trim_before"] = True
                token.fix["ensure_ws_after"] = True

                if (next_in_line and ws_after == 0) or \
                   (prev_in_line and ws_before > 0):
                    mh.style_issue(token.location,
                                   "comma cannot be preceeded by whitespace "
                                   "and must be followed by whitespace",
                                   True)

            if config.active(cfg, "eol_comma") and last_code_in_line:
                mh.style_issue(token.location,
                               "lines must not end with a comma")

        elif token.kind == "COLON":
            if config.active(cfg, "whitespace_colon"):
                token.fix["ensure_trim_before"] = True
                token.fix["ensure_trim_after"] = True

                if prev_in_line and prev_in_line.kind == "COMMA":
                    token.fix["ensure_trim_before"] = False
                    # We don't deal with this here. If anything it's the
                    # problem of the comma whitespace rules.
                else:
                    if ((prev_in_line and ws_before > 0) or
                        (next_in_line and ws_after > 0)):
                        mh.style_issue(token.location,
                                       "no whitespace around colon allowed",
                                       True)

        # Corresponds to the old CodeChecker EqualSignWhitespace rule
        elif token.kind == "ASSIGNMENT":
            if config.active(cfg, "whitespace_assignment"):
                token.fix["ensure_ws_before"] = True
                token.fix["ensure_ws_after"] = True

                if prev_in_line and ws_before == 0:
                    mh.style_issue(token.location,
                                   "= must be preceeded by whitespace",
                                   True)
                elif next_in_line and ws_after == 0:
                    mh.style_issue(token.location,
                                   "= must be succeeded by whitespace",
                                   True)

            if config.active(cfg, "builtin_shadow"):
                # Here we now try to figure out what we assigned to. In
                # the absence of parser we can just go backwards to the
                # last newline, reverse matching brackets on the way.
                brackets = []
                badness = []
                parens = 0
                for i in reversed(range(last_newline, n)):
                    if tbuf.tokens[i].kind in ("A_KET", "M_KET"):
                        brackets.append("]")
                    elif tbuf.tokens[i].kind == "KET":
                        brackets.append(")")
                        parens += 1
                    elif tbuf.tokens[i].kind in ("A_BRA", "M_BRA"):
                        if len(brackets) == 0:
                            # Almost certain a syntax error
                            break
                        elif brackets.pop() != "]":
                            break
                    elif tbuf.tokens[i].kind == "BRA":
                        if len(brackets) == 0:
                            # Syntax error or maybe classdef
                            break
                        elif brackets.pop() != ")":
                            break
                        parens -= 1
                    elif tbuf.tokens[i].kind == "COMMA" and len(brackets) == 0:
                        break
                    elif tbuf.tokens[i].kind == "IDENTIFIER" and parens == 0:
                        if tbuf.tokens[i].value() in BUILTIN_FUNCTIONS:
                            badness.append(tbuf.tokens[i])
                    elif tbuf.tokens[i].kind == "KEYWORD" and \
                         tbuf.tokens[i].value() == "for":
                        # If we find a for, then we're in a for loop. We
                        # special case i and j since they are so damn
                        # common.
                        badness = [t
                                   for t in badness
                                   if t.value() not in ("i", "j")]
                for tok in badness:
                    mh.style_issue(tok.location,
                                   "redefinition of builtin function is a"
                                   " very naughty thing to do")

        # Corresponds to the old CodeChecker ParenthesisWhitespace and
        # BracketsWhitespace rules
        elif token.kind in ("BRA", "A_BRA", "M_BRA"):
            if config.active(cfg, "whitespace_brackets") and \
               next_in_line and ws_after > 0 and \
               next_in_line.kind != "CONTINUATION":
                mh.style_issue(token.location,
                               "%s must not be followed by whitespace" %
                               token.raw_text,
                               True)
                token.fix["ensure_trim_after"] = True

        elif token.kind in ("KET", "A_KET", "M_KET"):
            if config.active(cfg, "whitespace_brackets") and \
               prev_in_line and ws_before > 0:
                mh.style_issue(token.location,
                               "%s must not be preceeded by whitespace" %
                               token.raw_text,
                               True)
                token.fix["ensure_trim_before"] = True

        # Corresponds to the old CodeChecker KeywordWhitespace rule
        elif (token.kind in ("KEYWORD", "IDENTIFIER") and
              token.value() in WORDS_WITH_WS):
            if config.active(cfg, "whitespace_keywords") and \
               next_in_line and ws_after == 0:
                mh.style_issue(token.location,
                               "keyword must be succeeded by whitespace",
                               True)
                token.fix["ensure_ws_after"] = True

            # Corresponds to the old CodeChecker FunctionName rule
            if token.kind == "KEYWORD" and token.value() == "function":
                try:
                    parser = Mini_Parser(tbuf, n)
                    parser.parse_function_declaration()
                except Error:
                    pass

        # Corresponds to the old CodeChecker CommentWhitespace rule
        elif token.kind == "COMMENT":
            if config.active(cfg, "whitespace_comments"):
                comment_char = token.raw_text[0]
                comment_body = token.raw_text.lstrip(comment_char)
                if re.match("^%#[a-zA-Z]", token.raw_text):
                    # Stuff like %#codegen or %#ok are pragmas and should
                    # not be subject to style checks
                    pass

                elif re.match("^%# +[a-zA-Z]", token.raw_text):
                    # This looks like a pragma, but there is a spurious
                    # space
                    mh.style_issue(token.location,
                                   "MATLAB pragma must not contain whitespace "
                                   "between %# and the pragma",
                                   True)
                    token.raw_text = "%#" + token.raw_text[2:].strip()

                elif re.match("^% +#[a-zA-Z]", token.raw_text):
                    # This looks like a pragma that got "fixed" before we
                    # fixed our pragma handling
                    mh.style_issue(token.location,
                                   "MATLAB pragma must not contain whitespace "
                                   "between % and the pragma",
                                   True)
                    token.raw_text = "%#" + token.raw_text.split("#", 1)[1]

                elif comment_body and not comment_body.startswith(" "):
                    # Normal comments should contain whitespace
                    mh.style_issue(token.location,
                                   "comment body must be separated with "
                                   "whitespace from the starting %s" %
                                   comment_char,
                                   True)
                    token.raw_text = (comment_char * (len(token.raw_text) -
                                                      len(comment_body)) +
                                      " " +
                                      comment_body)

                # Make sure we have whitespace before each comment
                if prev_in_line and ws_before == 0:
                    mh.style_issue(token.location,
                                   "comment must be preceeded by whitespace",
                                   True)
                    token.fix["ensure_ws_before"] = True

        elif token.kind == "CONTINUATION":
            # Make sure we have whitespace before each line continuation
            if config.active(cfg, "whitespace_continuation") and \
               prev_in_line and ws_before == 0:
                mh.style_issue(token.location,
                               "continuation must be preceeded by whitespace",
                               True)
                token.fix["ensure_ws_before"] = True

            if config.active(cfg, "operator_after_continuation") and \
               next_token and next_token.first_in_line and \
               next_token.kind == "OPERATOR":
                # Continuations should not start with operators unless
                # its a unary. Right now we can't tell (needs
                # parsing), so we under-approximate
                if prev_token and prev_token.kind == "OPERATOR":
                    pass
                elif prev_token and prev_token.kind == "ASSIGNMENT":
                    # x = ...
                    #    -potato (this is ok)
                    pass
                else:
                    mh.style_issue(next_token.location,
                                   "continuations should not start with "
                                   "operators")


def analyze(filename, rule_set, autofix):
    assert isinstance(filename, str)
    assert isinstance(autofix, bool)

    encoding = "cp1252"

    # Get config first, since we might want to skip this file

    cfg = config.get_config(filename)
    rule_lib = build_library(cfg, rule_set)

    if not cfg["enable"]:
        mh.register_exclusion(filename)
        return

    mh.register_file(filename)

    # Do some file-based sanity checking

    if not os.path.exists(filename):
        mh.error(Location(filename), "file does not exist")

    if not os.path.isfile(filename):
        mh.error(Location(filename), "is not a file")

    if not filename.endswith(".m"):
        mh.warning(Location(filename), "filename should end with '.m'")

    # Create lexer

    lexer = MATLAB_Lexer(filename, encoding=encoding)

    # We're dealing with an empty file here. Lets just not do anything

    if len(lexer.text.strip()) == 0:
        return

    # Stage 1 - rules around the file itself

    for rule in rule_lib["on_file"]:
        rule.apply(cfg, lexer.filename, lexer.context_line)

    # Stage 2 - rules around raw text lines

    for line_no, line in enumerate(lexer.context_line, 1):
        for rule in rule_lib["on_line"]:
            rule.apply(cfg, lexer.filename, line_no, line)

    # Tabs are just super annoying, and they require special
    # treatment. There is a known but obscure bug here, in that tabs
    # in strings are replaced as if they were part of normal
    # text. This is probably not intentional. For example:
    #
    # "a<tab>b"
    #    "a<tab>b"
    #
    # Will right now come out as
    #
    # "a   b"
    # "  a b"
    #
    # This is probably not correct. Fixing this is will require a very
    # different kind of lexing (which I am not in the mood for, I have
    # suffered enough to deal with ') or a 2-pass solution (which is
    # slow): first we lex and then fix up tabs inside tokens; and then
    # we do the global replacement and lex again before we proceed.

    if autofix:
        lexer.correct_tabs(cfg["tab_width"])

    # Create tokenbuffer

    try:
        tbuf = Token_Buffer(lexer)
    except Error:
        # If there are lex errors, we can stop here
        return

    # Stage 3 - rules around individual tokens

    stage_3_analysis(cfg, tbuf)

    # Re-write the file, with issues fixed

    if autofix:
        with open(filename, "w", encoding=encoding) as fd:
            tbuf.replay(fd)

    # Emit messages

    mh.flush_messages(filename)


def main():
    rule_set = get_rules()

    ap = argparse.ArgumentParser(
        description="MATLAB Independent Syntax and Semantics System")
    ap.add_argument("files",
                    metavar="FILE|DIR",
                    nargs="*",
                    help="MATLAB files or directories to analyze")
    ap.add_argument("--brief",
                    action="store_true",
                    default=False,
                    help="Don't show line-context on messages")
    ap.add_argument("--no-style",
                    action="store_true",
                    default=False,
                    help=("Don't show any style message, only show warnings "
                          "and errors."))
    ap.add_argument("--fix",
                    action="store_true",
                    default=False,
                    help="Automatically fix issues where the fix is obvious")
    ap.add_argument("--ignore-config",
                    action="store_true",
                    default=False,
                    help="Ignore all %s files." % config.CONFIG_FILENAME)
    ap.add_argument('--html',
                    default=None,
                    help="Write report to given file as HTML")
    style_option = ap.add_argument_group("Rule options")

    # Add any parameters from rules
    for rule_kind in rule_set:
        for rule in rule_set[rule_kind]:
            rule_params = getattr(rule, "parameters", None)
            if not rule_params:
                continue
            for p_name in rule_params:
                style_option.add_argument("--" + p_name,
                                          **rule_params[p_name])

    style_option.add_argument("--copyright-entity",
                              metavar="STR",
                              default=[],
                              nargs="+",
                              help=("Add (company) name to check for in "
                                    "Copyright notices. Can be specified "
                                    "multiple times."))

    options = ap.parse_args()

    if not options.brief and sys.stdout.encoding != "UTF-8":
        print("WARNING: It looks like your environment is not set up quite")
        print("         right since python will encode to %s on stdout." %
              sys.stdout.encoding)
        print()
        print("To fix set one of the following environment variables:")
        print("   LC_ALL=en_GB.UTF-8 (or something similar)")
        print("   PYTHONIOENCODING=UTF-8")

    if not options.files:
        ap.print_help()
        sys.exit(1)

    mh.show_context = not options.brief
    mh.show_style   = not options.no_style
    mh.autofix      = options.fix
    mh.html         = options.html is not None
    # mh.sort_messages = False

    for item in options.files:
        if os.path.isdir(item):
            config.register_tree(os.path.abspath(item))
        elif os.path.isfile(item):
            config.register_tree(os.path.dirname(os.path.abspath(item)))
        else:
            ap.error("%s is neither a file nor directory" % item)
    config.build_config_tree(build_default_config(rule_set),
                             options)

    for item in options.files:
        if os.path.isdir(item):
            for path, dirs, files in os.walk(item):
                dirs.sort()
                for f in sorted(files):
                    if f.endswith(".m"):
                        analyze(os.path.normpath(os.path.join(path, f)),
                                rule_set,
                                options.fix)
        else:
            analyze(os.path.normpath(item),
                    rule_set,
                    options.fix)

    if options.html is not None:
        mh.print_html_and_exit(options.html)
    else:
        mh.print_summary_and_exit()


def ice_handler():
    try:
        main()
    except ICE as internal_compiler_error:
        traceback.print_exc()
        print("-" * 70)
        print("- Encountered an internal compiler error. This is a tool")
        print("- bug, please report it on our github issues so we can fix it:")
        print("-")
        print("-    %s" % GITHUB_ISSUES)
        print("-")
        print("- Please include the above backtrace in your bug report, and")
        print("- the following information:")
        print("-")
        lines = textwrap.wrap(internal_compiler_error.reason)
        print("\n".join("- %s" % l for l in lines))
        print("-" * 70)


if __name__ == "__main__":
    ice_handler()
