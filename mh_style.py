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
        if self.peek("S_BRA"):
            out_brackets = True
            self.match("S_BRA")
            if self.peek("S_KET"):
                self.match("S_KET")
            else:
                while True:
                    returns.append(self.parse_selection(in_reference=True))
                    if self.peek("COMMA"):
                        self.match("COMMA")
                    else:
                        break
                self.match("S_KET")
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


def stage_1_analysis(cfg, lexer):
    assert isinstance(lexer, MATLAB_Lexer)

    lines = lexer.context_line

    # Corresponds to the old CodeChecker LineCount rule
    if len(lines) > cfg["file_length"]:
        mh.style_issue(Location(lexer.filename,
                                len(lines)),
                       "file exceeds %u lines" % cfg["file_length"])

    # Corresponds to the old CodeChecker EndingEmptyLine rule
    if len(lines) >= 2 and lines[-1] == "":
        mh.style_issue(Location(lexer.filename,
                                len(lines)),
                       "trailing blank lines at end of file")

    is_blank = False
    for n, line in enumerate(lines):
        # Corresponds to the old CodeChecker LineLength rule
        if len(line) > cfg["line_length"] + 1:
            mh.style_issue(Location(lexer.filename,
                                    n + 1,
                                    cfg["line_length"] + 1,
                                    len(line),
                                    line),
                           "line exceeds %u characters" % cfg["line_length"])

        # Corresponds to the old CodeChecker MultipleEmptyLines rule
        if len(line.strip()):
            is_blank = False
        elif is_blank:
            mh.style_issue(Location(lexer.filename,
                                    n + 1),
                           "more than one consecutive blank line")
        else:
            is_blank = True

        # Corresponds to the old CodeChecker TabIndentation rule
        #
        # It is actually a bit more aggressive, and bans the <tab>
        # character everywhere.
        if "\t" in line:
            mh.style_issue(Location(lexer.filename,
                                    n + 1,
                                    line.index("\t"),
                                    line.index("\t"),
                                    line),
                           "tab is not allowed")

        # Corresponds to the old CodeChecker TrailingWhitespaces and
        # EmptyLineRelativeIndentation rules.
        #
        # Since this tool can re-write easily, we've made it a bit
        # more strict: No trailing WS is allowed, so empty lines must
        # not contain any characters. Hence the MATLAB editor doesn't
        # really get in the way anymore, since you don't have to fix
        # it by hand.
        if line.endswith(" "):
            if len(line.strip()) == 0:
                mh.style_issue(Location(lexer.filename,
                                        n + 1),
                               "whitespace on blank line")
            else:
                mh.style_issue(Location(lexer.filename,
                                        n + 1,
                                        len(line.rstrip()),
                                        len(line),
                                        line),
                               "trailing whitespace")


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


def stage_2_analysis(cfg, tbuf):
    assert isinstance(tbuf, Token_Buffer)

    in_copyright_notice = True
    company_copyright_found = False
    generic_copyright_found = False
    copyright_token = None
    copyright_notice = []

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
            token.fix["ensure_trim_before"] = True
            token.fix["ensure_ws_after"] = True

            if last_code_in_line:
                mh.style_issue(token.location,
                               "lines must not end with a comma")

            if (next_in_line and ws_after == 0) or \
               (prev_in_line and ws_before > 0):
                mh.style_issue(token.location,
                               "comma cannot be preceeded by whitespace "
                               "and must be followed by whitespace")

        # Corresponds to the old CodeChecker EqualSignWhitespace rule
        elif token.kind == "ASSIGNMENT":
            token.fix["ensure_ws_before"] = True
            token.fix["ensure_ws_after"] = True
            if prev_in_line and ws_before == 0:
                mh.style_issue(token.location,
                               "= must be preceeded by whitespace")
            elif next_in_line and ws_after == 0:
                mh.style_issue(token.location,
                               "= must be succeeded by whitespace")

        # Corresponds to the old CodeChecker ParenthesisWhitespace and
        # BracketsWhitespace rules
        elif token.kind in ("BRA", "S_BRA"):
            if next_in_line and ws_after > 0 and \
               next_in_line.kind != "CONTINUATION":
                mh.style_issue(token.location,
                               "%s must not be followed by whitespace" %
                               token.raw_text)
                token.fix["ensure_trim_after"] = True

        elif token.kind in ("KET", "S_KET"):
            if prev_in_line and ws_before > 0:
                mh.style_issue(token.location,
                               "%s must not be preceeded by whitespace" %
                               token.raw_text)
                token.fix["ensure_trim_before"] = True

        # Corresponds to the old CodeChecker KeywordWhitespace rule
        elif (token.kind in ("KEYWORD", "IDENTIFIER") and
              token.value() in WORDS_WITH_WS):
            if next_in_line and ws_after == 0:
                mh.style_issue(token.location,
                               "keyword must be succeeded by whitespace")
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
                               "between %# and the pragma")
                token.raw_text = "%#" + token.raw_text[2:].strip()

            elif re.match("^% +#[a-zA-Z]", token.raw_text):
                # This looks like a pragma that got "fixed" before we
                # fixed our pragma handling
                mh.style_issue(token.location,
                               "MATLAB pragma must not contain whitespace "
                               "between % and the pragma")
                token.raw_text = "%#" + token.raw_text.split("#", 1)[1]

            elif comment_body and not comment_body.startswith(" "):
                # Normal comments should contain whitespace
                mh.style_issue(token.location,
                               "comment body must be separated with "
                               "whitespace from the starting %s" %
                               comment_char)
                token.raw_text = (comment_char * (len(token.raw_text) -
                                                  len(comment_body)) +
                                  " " +
                                  comment_body)

            # Make sure we have whitespace before each comment
            if prev_in_line and ws_before == 0:
                mh.style_issue(token.location,
                               "comment must be preceeded by whitespace")
                token.fix["ensure_ws_before"] = True

        elif token.kind == "CONTINUATION":
            # Make sure we have whitespace before each line continuation
            if prev_in_line and ws_before == 0:
                mh.style_issue(token.location,
                               "continuation must be preceeded by whitespace")
                token.fix["ensure_ws_before"] = True

        if (prev_token and prev_token.kind == "CONTINUATION" and
            token.first_in_line and token.kind == "OPERATOR"):
            mh.style_issue(token.location,
                           "continuations should not start with operators")


def analyze(filename, autofix):
    assert isinstance(filename, str)
    assert isinstance(autofix, bool)

    encoding = "cp1252"

    # Get config first, since we might want to skip this file

    cfg = config.get_config(filename)

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

    # Get configuration and create lexer

    lexer = MATLAB_Lexer(filename, encoding=encoding)

    # We're dealing with an empty file here. Lets just not do anything

    if len(lexer.text.strip()) == 0:
        return

    # Stage 1 - rules around lines and the file itself. This doesn't
    # require any lexing yet.

    stage_1_analysis(cfg, lexer)

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

    # Stange 2. Look at raw token stream for some of the more basic
    # rules.

    stage_2_analysis(cfg, tbuf)

    # Re-write the file, with issues fixed

    if autofix:
        with open(filename, "w", encoding=encoding) as fd:
            tbuf.replay(fd)

    # Emit messages

    mh.flush_messages(filename)


def main():
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
    style_option = ap.add_argument_group("Style options")
    style_option.add_argument("--line-length",
                              metavar="N",
                              default=None,
                              type=int,
                              help=("Maximum line length, %u by default." %
                                    config.DEFAULT["line_length"]))
    style_option.add_argument("--file-length",
                              metavar="N",
                              default=None,
                              type=int,
                              help=("Maximum number of lines per file, "
                                    "%u by default." %
                                    config.DEFAULT["file_length"]))
    style_option.add_argument("--tab-width",
                              metavar="N",
                              default=None,
                              type=int,
                              help=("Consider tabs to be N spaces wide, "
                                    "%u by default." %
                                    config.DEFAULT["tab_width"]))
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
    # mh.sort_messages = False

    try:
        for item in options.files:
            if os.path.isdir(item):
                config.register_tree(os.path.abspath(item))
            elif os.path.isfile(item):
                config.register_tree(os.path.dirname(os.path.abspath(item)))
            else:
                ap.error("%s is neither a file nor directory" % item)
        config.build_config_tree(options)

        for item in options.files:
            if os.path.isdir(item):
                for path, dirs, files in os.walk(item):
                    dirs.sort()
                    for f in sorted(files):
                        if f.endswith(".m"):
                            analyze(os.path.normpath(os.path.join(path, f)),
                                    options.fix)
            else:
                analyze(os.path.normpath(item), options.fix)

        mh.print_summary_and_exit()

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
    main()
