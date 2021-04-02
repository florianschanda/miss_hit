#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2019-2021, Florian Schanda                    ##
##              Copyright (C) 2019-2020, Zenuity AB                         ##
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

import os
import re
from copy import copy

from abc import ABCMeta, abstractmethod

from miss_hit_core import work_package
from miss_hit_core import command_line
from miss_hit_core import config

from miss_hit_core.errors import (Location, Error, ICE,
                                  Message_Handler,
                                  HTML_Message_Handler,
                                  JSON_Message_Handler)
from miss_hit_core.m_ast import *
from miss_hit_core.m_lexer import MATLAB_Lexer, Token_Buffer
from miss_hit_core.m_parser import MATLAB_Parser
from miss_hit_core.m_parse_utils import parse_docstrings


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
    def apply(self, mh, cfg, filename, full_text, lines):
        pass


class Style_Rule_Line(Style_Rule):
    @abstractmethod
    def apply(self, mh, cfg, filename, line_no, line):
        pass


class Rule_File_Length(Style_Rule_File):
    """Maximum file length

    This is configurable with 'file_length'. It is a good idea to keep
    the length of your files under some limit since it forces your
    project into avoiding the worst spaghetti code.

    """

    parameters = {
        "file_length": {
            "type"    : int,
            "metavar" : "N",
            "help"    : ("Maximum lines in a file, %u by default." %
                         config.STYLE_CONFIGURATION["file_length"].default)
        }
    }

    defaults = {
        "file_length" : config.STYLE_CONFIGURATION["file_length"].default,
    }

    def __init__(self):
        super().__init__("file_length")

    def apply(self, mh, cfg, filename, full_text, lines):
        if len(lines) > cfg.style_config["file_length"]:
            mh.style_issue(Location(filename,
                                    len(lines)),
                           "file exceeds %u lines" %
                           cfg.style_config["file_length"],
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

    def apply(self, mh, cfg, filename, full_text, lines):
        if len(lines) >= 2 and lines[-1] == "":
            mh.style_issue(Location(filename,
                                    len(lines)),
                           "trailing blank lines at end of file",
                           self.autofix)
        elif len(full_text) and full_text[-1] != "\n":
            mh.style_issue(Location(filename,
                                    len(lines)),
                           "file should end with a new line",
                           self.autofix)


class Rule_Line_Length(Style_Rule_Line):
    """Max characters per line

    This is configurable with 'line_length', default is 80. It is a
    good idea for readability to avoid overly long lines. This can help
    you avoid extreme levels of nesting and avoids having to scroll
    around.

    """

    parameters = {
        "line_length": {
            "type"    : int,
            "metavar" : "N",
            "help"    : ("Maximum characters per line, %u by default." %
                         config.STYLE_CONFIGURATION["line_length"].default),
        }
    }

    defaults = {
        "line_length" : config.STYLE_CONFIGURATION["line_length"].default,
    }

    def __init__(self):
        super().__init__("line_length", False)

    def apply(self, mh, cfg, filename, line_no, line):
        if len(line) > cfg.style_config["line_length"]:
            mh.style_issue(Location(filename,
                                    line_no,
                                    cfg.style_config["line_length"],
                                    len(line),
                                    line),
                           "line exceeds %u characters" %
                           cfg.style_config["line_length"],
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

    def apply(self, mh, cfg, filename, line_no, line):
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
    but this can be configured with the options 'tab_width'.

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
            "help"    : ("Tab-width, by default %u." %
                         config.STYLE_CONFIGURATION["tab_width"].default),
        }
    }

    defaults = {
        "tab_width" : config.STYLE_CONFIGURATION["tab_width"].default,
    }

    def __init__(self):
        super().__init__("tabs", True)
        self.mandatory = True

    def apply(self, mh, cfg, filename, line_no, line):
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

    def apply(self, mh, cfg, filename, line_no, line):
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
            if inst.mandatory or cfg.active(inst.name):
                lib[kind].append(inst)

    return lib


##############################################################################


KEYWORDS_WITH_WS = frozenset([
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

    # These are not keywords all the time, but we treat them like it.
    "properties",
    "methods",
    "events",
])


def stage_3_analysis(mh, cfg, tbuf, is_embedded, fixed, valid_code):
    assert isinstance(mh, Message_Handler)
    assert isinstance(tbuf, Token_Buffer)
    assert isinstance(is_embedded, bool)
    assert isinstance(fixed, bool)
    assert isinstance(valid_code, bool)

    # Some state needed to fix indentation
    statement_start_token = None
    current_indent = 0
    enclosing_ast = None
    bracket_stack = []
    relevant_brackets = set()

    # Find out which brackets are relevant for us for aligning
    # continuations
    if cfg.active("indentation"):
        if cfg.style_config["align_round_brackets"]:
            relevant_brackets.add("BRA")
        if cfg.style_config["align_other_brackets"]:
            relevant_brackets.add("M_BRA")
            relevant_brackets.add("C_BRA")

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

        # Keep track of statement starters. This is required for
        # indentation.
        if valid_code and token.first_in_statement:
            # We need to take special care of comments that are the
            # first thing after an open block. Since comments are not
            # attached to the AST (and it is not practical to do so),
            # most of the time we can just indent them to "same as
            # above". But if they are the first item inside e.g. an if
            # statement, then this won't work (the previous
            # indentation level is one too low).
            if statement_start_token and \
               statement_start_token.kind == "KEYWORD" and \
               statement_start_token.value == "end":
                # The previous token was 'end'. We don't need to
                # do anything in this case, since we'll re-use the
                # indentation level of the compound statement
                enclosing_ast = None
            elif statement_start_token and \
                 statement_start_token.ast_link and \
                 statement_start_token.ast_link.causes_indentation():
                # We've got a previous AST node. We remember it,
                # and indent one level below it, but only if it is
                # a statement that would create nesting.
                enclosing_ast = statement_start_token.ast_link

            statement_start_token = token

        # Recognize justifications
        if token.kind in ("COMMENT", "CONTINUATION"):
            if "mh:ignore_style" in token.value:
                mh.register_justification(token)

        # Don't ever check anonymous tokens
        if token.anonymous:
            continue

        # Corresponds to the old CodeChecker CommaWhitespace
        # rule. CommaLineEndings is now folded into the new
        # end_of_statements rule, which is much more strict and
        # complete.
        if token.kind == "COMMA":
            if cfg.active("whitespace_comma"):
                token.fix.ensure_trim_before = True
                token.fix.ensure_ws_after = True

                if (next_in_line and ws_after == 0) or \
                   (prev_in_line and ws_before > 0):
                    mh.style_issue(token.location,
                                   "comma cannot be preceeded by whitespace "
                                   "and must be followed by whitespace",
                                   fixed)

            if cfg.active("spurious_row_comma") and token.fix.spurious:
                token.fix.delete = True
                mh.style_issue(token.location,
                               "this comma is not required and can be removed",
                               fixed)

        elif token.kind == "SEMICOLON":
            if cfg.active("whitespace_semicolon"):
                token.fix.ensure_trim_before = True
                token.fix.ensure_ws_after = True

                if (next_in_line and ws_after == 0) or \
                   (prev_in_line and ws_before > 0):
                    mh.style_issue(token.location,
                                   "semicolon cannot be preceeded by "
                                   "whitespace and must be followed by "
                                   "whitespace",
                                   fixed)

            if cfg.active("spurious_row_semicolon") and token.fix.spurious:
                token.fix.delete = True
                mh.style_issue(token.location,
                               "this semicolon is not required and can "
                               "be removed",
                               fixed)

        elif token.kind == "COLON":
            if cfg.active("whitespace_colon"):
                if prev_in_line and prev_in_line.kind == "COMMA":
                    pass
                    # We don't deal with this here. If anything it's the
                    # problem of the comma whitespace rules.
                elif next_in_line and \
                     next_in_line.kind == "CONTINUATION":
                    # Special exception in the rare cases we
                    # continue a range expression
                    if prev_in_line and ws_before > 0:
                        token.fix.ensure_trim_before = True
                        mh.style_issue(token.location,
                                       "no whitespace before colon",
                                       fixed)
                elif (prev_in_line and ws_before > 0) or \
                     (next_in_line and ws_after > 0):
                    token.fix.ensure_trim_before = True
                    token.fix.ensure_trim_after = True
                    mh.style_issue(token.location,
                                   "no whitespace around colon"
                                   " allowed",
                                   fixed)

        # Corresponds to the old CodeChecker EqualSignWhitespace rule
        elif token.kind == "ASSIGNMENT":
            if cfg.active("whitespace_assignment"):
                token.fix.ensure_ws_before = True
                token.fix.ensure_ws_after = True

                if prev_in_line and ws_before == 0:
                    mh.style_issue(token.location,
                                   "= must be preceeded by whitespace",
                                   fixed)
                elif next_in_line and ws_after == 0:
                    mh.style_issue(token.location,
                                   "= must be succeeded by whitespace",
                                   fixed)

        # Corresponds to the old CodeChecker ParenthesisWhitespace and
        # BracketsWhitespace rules
        elif token.kind in ("BRA", "A_BRA", "M_BRA"):
            if cfg.active("whitespace_brackets") and \
               next_in_line and ws_after > 0 and \
               next_in_line.kind != "CONTINUATION":
                mh.style_issue(token.location,
                               "%s must not be followed by whitespace" %
                               token.raw_text,
                               fixed)
                token.fix.ensure_trim_after = True

        elif token.kind in ("KET", "A_KET", "M_KET"):
            if cfg.active("whitespace_brackets") and \
               prev_in_line and ws_before > 0:
                mh.style_issue(token.location,
                               "%s must not be preceeded by whitespace" %
                               token.raw_text,
                               fixed)
                token.fix.ensure_trim_before = True

        elif token.kind == "KEYWORD":
            # Corresponds to the old CodeChecker KeywordWhitespace rule
            if token.value in KEYWORDS_WITH_WS and \
               cfg.active("whitespace_keywords") and \
               next_in_line and ws_after == 0:
                mh.style_issue(token.location,
                               "keyword must be succeeded by whitespace",
                               fixed)
                token.fix.ensure_ws_after = True

            # Make sure we have whitespace _before_ the function
            # keyword
            if token.value == "function" and \
               cfg.active("whitespace_around_functions"):
                # There is a special exception here for comments
                # before functions
                true_fstart_token = token
                true_fstart_prev_token = prev_token
                for i in reversed(range(0, n)):
                    if tbuf.tokens[i].kind == "COMMENT" and \
                       tbuf.tokens[i].first_in_line:
                        true_fstart_token = tbuf.tokens[i]
                        if i > 0:
                            true_fstart_prev_token = tbuf.tokens[i - 1]
                        else:
                            true_fstart_prev_token = None
                    elif tbuf.tokens[i].kind == "NEWLINE" and \
                         tbuf.tokens[i].value.count("\n") == 1:
                        pass
                    else:
                        break

                if true_fstart_prev_token and \
                   not (true_fstart_prev_token.location.line + 1 <
                        true_fstart_token.location.line):
                    true_fstart_prev_token.fix.add_newline = True
                    mh.style_issue(token.location,
                                   "function should be preceeded by an empty"
                                   " line",
                                   fixed)

            # Make sure we have whitespace _after_ the function end
            if valid_code and \
               token.value == "end" and \
               cfg.active("whitespace_around_functions") and \
               isinstance(token.ast_link, Function_Definition):
                # We first need to find the actual last token on this line
                true_end_id = n
                true_end_next = None
                true_end_nl = None
                for i in range(n + 1, len(tbuf.tokens)):
                    if tbuf.tokens[i].kind == "NEWLINE":
                        true_end_nl = tbuf.tokens[i]
                        break
                    elif tbuf.tokens[i].location.line == token.location.line:
                        true_end_id = i
                    else:
                        break
                true_end = tbuf.tokens[true_end_id]
                for i in range(true_end_id + 1, len(tbuf.tokens)):
                    if tbuf.tokens[i].kind == "NEWLINE":
                        pass
                    else:
                        true_end_next = tbuf.tokens[i]
                        break

                if true_end_next and \
                   not (true_end.location.line + 1 <
                        true_end_next.location.line):
                    mh.style_issue(token.location,
                                   "function should be suceeded by an"
                                   " empty line",
                                   fixed)
                    if true_end_nl:
                        true_end_nl.fix.add_newline = True
                    else:
                        true_end.fix.add_newline = True

        # Corresponds to the old CodeChecker CommentWhitespace rule
        elif token.kind == "COMMENT":
            if cfg.active("whitespace_comments"):
                comment_char = token.raw_text[0]
                comment_body = token.raw_text.lstrip(comment_char)
                if re.match("^%#[a-zA-Z]", token.raw_text):
                    # Stuff like %#codegen or %#ok are pragmas and should
                    # not be subject to style checks
                    pass

                elif token.raw_text.startswith("%|"):
                    # This is a miss-hit pragma, but we've not
                    # processed it. This is fine.
                    pass

                elif token.block_comment:
                    # Ignore block comments
                    pass

                elif token.raw_text.strip() in ("%s%s" % (cc, cb)
                                                for cc in tbuf.comment_char
                                                for cb in "{}"):
                    # Leave block comment indicators alone
                    pass

                elif re.match("^%# +[a-zA-Z]", token.raw_text):
                    # This looks like a pragma, but there is a spurious
                    # space
                    mh.style_issue(token.location,
                                   "MATLAB pragma must not contain whitespace "
                                   "between %# and the pragma",
                                   fixed)
                    token.raw_text = "%#" + token.raw_text[2:].strip()

                elif re.match("^% +#[a-zA-Z]", token.raw_text):
                    # This looks like a pragma that got "fixed" before we
                    # fixed our pragma handling
                    mh.style_issue(token.location,
                                   "MATLAB pragma must not contain whitespace "
                                   "between % and the pragma",
                                   fixed)
                    token.raw_text = "%#" + token.raw_text.split("#", 1)[1]

                elif comment_body and not comment_body.startswith(" "):
                    # Normal comments should contain whitespace
                    mh.style_issue(token.location,
                                   "comment body must be separated with "
                                   "whitespace from the starting %s" %
                                   comment_char,
                                   fixed)
                    token.raw_text = (comment_char * (len(token.raw_text) -
                                                      len(comment_body)) +
                                      " " +
                                      comment_body)

                # Make sure we have whitespace before each comment
                if prev_in_line and ws_before == 0:
                    mh.style_issue(token.location,
                                   "comment must be preceeded by whitespace",
                                   fixed)
                    token.fix.ensure_ws_before = True

        elif token.kind == "CONTINUATION":
            # Make sure we have whitespace before each line continuation
            if cfg.active("whitespace_continuation") and \
               prev_in_line and ws_before == 0:
                mh.style_issue(token.location,
                               "continuation must be preceeded by whitespace",
                               fixed)
                token.fix.ensure_ws_before = True

            if cfg.active("operator_after_continuation") and \
               next_token and next_token.first_in_line and \
               next_token.kind == "OPERATOR" and \
               next_token.fix.binary_operator:
                # Continuations should not start with operators unless
                # its a unary.
                mh.style_issue(next_token.location,
                               "continuations should not start with binary "
                               "operators")

            if cfg.active("useless_continuation"):
                if next_token and next_token.kind in ("NEWLINE", "COMMENT"):
                    # Continuations followed immediately by a new-line
                    # or comment are not actually helpful at all.
                    mh.style_issue(token.location,
                                   "useless line continuation",
                                   fixed)
                    token.fix.replace_with_newline = True
                elif prev_token and prev_token.fix.statement_terminator:
                    mh.style_issue(token.location,
                                   "useless line continuation",
                                   fixed)
                    token.fix.delete = True

        elif token.kind == "OPERATOR":
            if not cfg.active("operator_whitespace"):
                pass
            elif token.fix.unary_operator:
                if (prev_in_line and ws_before > 0) and \
                   token.value in (".'", "'"):
                    mh.style_issue(token.location,
                                   "suffix operator must not be preceeded by"
                                   " whitespace",
                                   fixed)
                    token.fix.ensure_trim_before = True
                elif (next_in_line and ws_after > 0) and \
                     token.value not in (".'", "'"):
                    mh.style_issue(token.location,
                                   "unary operator must not be followed by"
                                   " whitespace",
                                   fixed)
                    token.fix.ensure_trim_after = True
            elif token.fix.binary_operator:
                if token.value in (".^", "^"):
                    if (prev_in_line and ws_before > 0) or \
                       (next_in_line and ws_after > 0):
                        mh.style_issue(token.location,
                                       "power binary operator"
                                       " must not be surrounded by whitespace",
                                       fixed)
                        token.fix.ensure_trim_before = True
                        token.fix.ensure_trim_after = True
                else:
                    if (prev_in_line and ws_before == 0) or \
                       (next_in_line and ws_after == 0):
                        mh.style_issue(token.location,
                                       "non power binary operator"
                                       " must be surrounded by whitespace",
                                       fixed)
                        token.fix.ensure_ws_before = True
                        token.fix.ensure_ws_after = True

            if valid_code and \
               cfg.active("implicit_shortcircuit") and \
               token.value in ("&", "|") and \
               token.ast_link and \
               isinstance(token.ast_link, Binary_Logical_Operation) and \
               token.ast_link.short_circuit:
                # This rule is *disabled* for now since it does not
                # work in all circumstances. Curiously, this bug is
                # shared by mlint which also mis-classifies & when
                # applied to arrays.
                #
                # To fix this we need to perform semantic analysis and
                # type inference. We're leaving this in for
                # compatibility with miss_hit.cfg files that contain
                # reference to this rules.
                #
                # mh.style_issue(token.location,
                #                "implicit short-circuit operation due to"
                #                " expression being contained in "
                #                " if/while guard",
                #                True)
                # token.fix.make_shortcircuit_explicit = True
                pass

        elif token.kind == "ANNOTATION":
            if cfg.active("annotation_whitespace"):
                token.fix.ensure_ws_after = True

                if next_in_line and ws_after == 0:
                    mh.style_issue(token.location,
                                   "annotation indication must be succeeded"
                                   " by whitespace",
                                   fixed)

        elif token.kind == "NEWLINE":
            if n == 0 and cfg.active("no_starting_newline"):
                # Files should not *start* with newline(s)
                mh.style_issue(token.location,
                               "files should not start with a newline",
                               fixed)
                token.fix.delete = True

        # Check some specific problems with continuations
        if token.fix.flag_continuations and \
           next_in_line and next_in_line.kind == "CONTINUATION":
            continuation_is_fixed = False
            token.fix.add_newline = False
            if cfg.active("dangerous_continuation"):
                next_in_line.fix.replace_with_newline = True
                continuation_is_fixed = True
            mh.style_issue(next_in_line.location,
                           "this continuation is dangerously misleading",
                           fixed and continuation_is_fixed)

        # Complain about indentation
        if valid_code and \
           cfg.active("indentation") and \
           token.kind != "NEWLINE":
            # Normally we ignore block comments, but the opening token
            # _is_ checked, as that one should align somehow.
            if token.first_in_line and not (token.block_comment and
                                            token.value != "{"):
                if token.first_in_statement:
                    if token.ast_link:
                        current_indent = token.ast_link.get_indentation()
                    elif enclosing_ast:
                        current_indent = enclosing_ast.get_indentation() + 1
                    offset = 0

                elif bracket_stack and \
                     bracket_stack[-1].kind in relevant_brackets and \
                     token.kind != "ANNOTATION":
                    # For stuff inside a bracket group we care about,
                    # we align it with the opening brace + 1, except
                    # for the closing brace, that one we align exactly
                    # with the opening brace.
                    if bracket_stack[-1].fix.correct_indent is not None:
                        offset = bracket_stack[-1].fix.correct_indent - \
                            statement_start_token.location.col_start
                    else:
                        offset = bracket_stack[-1].location.col_start - \
                            statement_start_token.location.col_start

                    if token.kind not in ("KET", "M_KET", "C_KET"):
                        offset += 1

                else:
                    # This is a continued line. We try to preserve
                    # the offset. We work out how much extra space
                    # this token has based on the statement
                    # starting token.
                    offset = token.location.col_start - \
                        statement_start_token.location.col_start

                    if offset <= 0 and not token.annotation:
                        # If positive, we can just add it. If 0 or
                        # negative, then we add 1/2 tabs to continue
                        # the line, since previously it was not offset
                        # at all.
                        offset = cfg.style_config["tab_width"] // 2
                    elif token.annotation:
                        # However, for annotations, the correct offset
                        # is to always align with the opening %|
                        # token. Ideally we will also do indentation
                        # for the stuff inside annotation block, but
                        # since we just have pragmas right now, this
                        # can wait. But this will be nasty. :(
                        offset = 0

                correct_spaces = (cfg.style_config["tab_width"] *
                                  current_indent +
                                  offset)
                token.fix.correct_indent = correct_spaces

                if token.location.col_start != correct_spaces:
                    mh.style_issue(token.location,
                                   "indentation not correct, should be"
                                   " %u spaces, not %u" %
                                   (correct_spaces,
                                    token.location.col_start),
                                   fixed)

        # Keep track of matrix and cell expressions. Again, required
        # for indentation. We do this *after* the fixing so we have a
        # chance to deal with the closing brackets while knowing the
        # opening brace, and the opening braces considering the
        # context we're currently in.
        if token.kind in ("M_BRA", "C_BRA", "BRA"):
            bracket_stack.append(token)
        elif token.kind in ("M_KET", "C_KET", "KET"):
            bracket_stack.pop()

        # Finally, check for unicode problems.
        if cfg.active("unicode") and \
           (cfg.style_config["enforce_encoding_comments"] or
            token.kind not in ("COMMENT", "CONTINUATION")):
            try:
                token.raw_text.encode(cfg.style_config["enforce_encoding"])
            except UnicodeEncodeError as uee:
                new_location = copy(token.location)
                new_location.col_start = token.location.col_start + uee.start
                new_location.col_end = token.location.col_start + (uee.end - 1)
                mh.style_issue(new_location,
                               "non-%s character in source" %
                               cfg.style_config["enforce_encoding"])


def check_copyright(mh, cfg, parse_tree, is_embedded):
    assert isinstance(mh, Message_Handler)
    assert isinstance(parse_tree, Compilation_Unit)
    assert isinstance(is_embedded, bool)

    # If the rule is turned off, do nothing
    if not cfg.active("copyright_notice"):
        return

    # Embedded code is only checked if requested
    if is_embedded and not cfg.style_config["copyright_in_embedded_code"]:
        return

    # Check copyright in docstrings. First we need to find the primary
    # entity. Note that in the file_header setting we ignore the
    # primary entities.
    location_kind = "docstring"
    if cfg.style_config["copyright_location"] == "file_header":
        n_primary = parse_tree
        n_docstring = parse_tree.n_docstring
        location_kind = "file header"
    elif isinstance(parse_tree, Function_File):
        n_primary = parse_tree.l_functions[0]
        n_docstring = n_primary.n_docstring
    elif isinstance(parse_tree, Class_File):
        n_primary = parse_tree.n_classdef
        n_docstring = n_primary.n_docstring
    else:
        n_primary = parse_tree
        n_docstring = parse_tree.n_docstring

    # If we couldn't find one, we fall back on the file docstring
    if n_docstring is None or not n_docstring.copyright_info:
        n_docstring = parse_tree.n_docstring

    # If we've called this function, we do check copyright notices. We
    # expect to find at least a docstring of some kind
    if n_docstring is None:
        mh.style_issue(n_primary.loc(),
                       "Could not find any copyright notice")
        return

    # We need to check that we only have one location with copyright
    # information
    if parse_tree.n_docstring:
        if parse_tree.n_docstring != n_docstring and \
           parse_tree.n_docstring.copyright_info and \
           n_docstring.copyright_info:
            mh.style_issue(n_primary.loc(),
                           "Copyright info should be in EITHER file header"
                           " or primary docstring, but not both")

    mentioned_entities = n_docstring.get_all_copyright_holders()

    # If we've called this function, we do check copyright notices. At
    # the least, we require there to be any kind of statement.
    if len(mentioned_entities) == 0:
        mh.style_issue(n_docstring.loc(),
                       "No copyright notice found in %s" % location_kind)
        return

    # If any copyright entities have been provided, we make sure that
    # any notices do match these
    allowed_entities = (cfg.style_config["copyright_entity"] |
                        cfg.style_config["copyright_3rd_party_entity"])
    if cfg.style_config["copyright_primary_entity"]:
        allowed_entities.add(cfg.style_config["copyright_primary_entity"])
    if len(allowed_entities) == 1:
        choices = list(allowed_entities)[0]
    elif len(allowed_entities) > 1:
        sorted_choices = list(sorted(allowed_entities))
        choices = ", ".join(sorted_choices[:-1])
        choices = "one of %s, or %s" % (choices, sorted_choices[-1])

    if allowed_entities:
        for n_info in n_docstring.copyright_info:
            if n_info.get_org() not in allowed_entities:
                mh.style_issue(n_info.loc_org(),
                               "Copyright entity '%s' is not %s"
                               % (n_info.get_org(), choices))


def stage_4_analysis(mh, cfg, parse_tree, is_embedded):
    assert isinstance(mh, Message_Handler)
    assert isinstance(parse_tree, Compilation_Unit)
    assert isinstance(is_embedded, bool)

    check_copyright(mh, cfg, parse_tree, is_embedded)


class MH_Style_Result(work_package.Result):
    def __init__(self, wp):
        super().__init__(wp, True)


class MH_Style(command_line.MISS_HIT_Back_End):
    def __init__(self):
        super().__init__("MH Style")

    @classmethod
    def process_wp(cls, wp):
        rule_set = wp.extra_options["rule_set"]
        autofix = wp.options.fix
        fd_tree = wp.extra_options["fd_tree"]
        debug_validate_links = wp.options.debug_validate_links

        # Build rule library

        rule_lib = build_library(wp.cfg, rule_set)

        # Load file content

        content = wp.get_content()

        # Create lexer

        lexer = MATLAB_Lexer(wp.mh, content, wp.filename, wp.blockname)
        if wp.cfg.octave:
            lexer.set_octave_mode()
        if not wp.cfg.pragmas:
            lexer.process_pragmas = False

        # We're dealing with an empty file here. Lets just not do anything

        if len(lexer.text.strip()) == 0:
            return MH_Style_Result(wp)

        # Stage 1 - rules around the file itself

        for rule in rule_lib["on_file"]:
            rule.apply(wp.mh, wp.cfg,
                       lexer.filename,
                       lexer.text,
                       lexer.context_line)

        # Stage 2 - rules around raw text lines

        for line_no, line in enumerate(lexer.context_line, 1):
            for rule in rule_lib["on_line"]:
                rule.apply(wp.mh, wp.cfg,
                           lexer.filename,
                           line_no,
                           line)

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
            lexer.correct_tabs(wp.cfg.style_config["tab_width"])

        # Create tokenbuffer

        try:
            tbuf = Token_Buffer(lexer, wp.cfg)
        except Error:
            # If there are lex errors, we can stop here
            return MH_Style_Result(wp)

        # Create parse tree

        try:
            parser = MATLAB_Parser(wp.mh, tbuf, wp.cfg)
            parse_tree = parser.parse_file()

            # Check naming (we do this after parsing, not during,
            # since we may need to re-write functions without end).
            parse_tree.sty_check_naming(wp.mh, wp.cfg)

            # Parse docstrings and attach them to the AST
            parse_docstrings(wp.mh, wp.cfg, parse_tree, tbuf)

            if debug_validate_links:
                tbuf.debug_validate_links()

            if fd_tree:
                fd_tree.write("-- Parse tree for %s\n" % wp.filename)
                parse_tree.pp_node(fd_tree)
                fd_tree.write("\n\n")

        except Error:
            parse_tree = None

        # Stage 3 - rules around individual tokens

        stage_3_analysis(
            mh          = wp.mh,
            cfg         = wp.cfg,
            tbuf        = tbuf,
            is_embedded = isinstance(wp, work_package.Embedded_MATLAB_WP),
            fixed       = parse_tree is not None,
            valid_code  = parse_tree is not None)

        # Stage 4 - rules involving the parse tree

        if parse_tree:
            stage_4_analysis(
                mh          = wp.mh,
                cfg         = wp.cfg,
                parse_tree  = parse_tree,
                is_embedded = isinstance(wp, work_package.Embedded_MATLAB_WP))

        # Possibly re-write the file, with issues fixed

        if autofix:
            if not parse_tree:
                wp.mh.error(lexer.get_file_loc(),
                            "file is not auto-fixed because it contains"
                            " parse errors",
                            fatal=False)
            else:
                # TODO: call modify()
                wp.write_modified(tbuf.replay())

        # Return results

        return MH_Style_Result(wp)


def main_handler():
    rule_set = get_rules()
    clp = command_line.create_basic_clp()

    clp["ap"].add_argument("--fix",
                           action="store_true",
                           default=False,
                           help=("Automatically fix issues where the fix"
                                 " is obvious"))

    clp["ap"].add_argument("--process-slx",
                           action="store_true",
                           default=False,
                           help=("Style-check (but not yet auto-fix) code"
                                 " inside SIMULINK models. This option is"
                                 " temporary, and will be removed in"
                                 " future once the feature is good enough"
                                 " to be enabled by default."))

    # Extra output options
    clp["output_options"].add_argument(
        "--html",
        default=None,
        help="Write report to given file as HTML")
    clp["output_options"].add_argument(
        "--json",
        default=None,
        help="Produce JSON report")
    clp["output_options"].add_argument(
        "--no-style",
        action="store_true",
        default=False,
        help="Don't show any style message, only show warnings and errors.")

    # Debug options
    clp["debug_options"].add_argument(
        "--debug-dump-tree",
        default=None,
        metavar="FILE",
        help="Dump text-based parse tree to given file")
    clp["debug_options"].add_argument(
        "--debug-validate-links",
        action="store_true",
        default=False,
        help="Debug option to check AST links")

    style_option = clp["ap"].add_argument_group("rule options")

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

    options = command_line.parse_args(clp)

    if options.html:
        if options.json:
            clp["ap"].error("Cannot produce JSON and HTML at the same time")
        if os.path.exists(options.html) and not os.path.isfile(options.html):
            clp["ap"].error("Cannot write to %s: it is not a file" %
                            options.html)
        mh = HTML_Message_Handler("style", options.html)
    elif options.json:
        if os.path.exists(options.json) and not os.path.isfile(options.json):
            clp["ap"].error("Cannot write to %s: it is not a file" %
                            options.json)
        mh = JSON_Message_Handler("style", options.json)
    else:
        mh = Message_Handler("style")

    mh.show_context = not options.brief
    mh.show_style   = not options.no_style
    mh.autofix      = options.fix

    extra_options = {
        "fd_tree"  : None,
        "rule_set" : rule_set,
    }

    if options.debug_dump_tree:
        extra_options["fd_tree"] = open(options.debug_dump_tree, "w")

    style_backend = MH_Style()
    command_line.execute(mh, options, extra_options,
                         style_backend,
                         options.process_slx)

    if options.debug_dump_tree:
        extra_options["fd_tree"].close()


def main():
    command_line.ice_handler(main_handler)


if __name__ == "__main__":
    main()
