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

from m_lexer import MATLAB_Token, MATLAB_Lexer, Token_Buffer
from errors import Location, mh
import config

COPYRIGHT_REGEX = r"(\(c\) )?Copyright (\d\d\d\d-)?\d\d\d\d *(?P<org>.*)"

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


def stage_2_analysis(cfg, tb):
    assert isinstance(tb, Token_Buffer)

    in_copyright_notice = True
    company_copyright_found = False
    generic_copyright_found = False
    copyright_token = None
    copyright_notice = []

    for n, token in enumerate(tb.tokens):
        if (n - 1 >= 0 and
            tb.tokens[n - 1].location.line == token.location.line):
            prev_in_line = tb.tokens[n - 1]
            ws_before = (token.location.col_start -
                         prev_in_line.location.col_end) - 1

        else:
            prev_in_line = None
            ws_before = None

        if (n + 1 < len(tb.tokens) and
            tb.tokens[n + 1].location.line == token.location.line):
            if tb.tokens[n + 1].kind == "NEWLINE":
                next_in_line = None
                ws_after = None
            else:
                next_in_line = tb.tokens[n + 1]
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
                    for s in ("(c)", "copyright"):
                        if s in token.value().lower():
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

        # Corresponds to the old CodeChecker CommentWhitespace rule
        elif token.kind == "COMMENT":
            comment_char = token.raw_text[0]
            comment_body = token.raw_text.lstrip(comment_char)
            if token.raw_text.startswith("%#codegen"):
                pass
            elif comment_body and not comment_body.startswith(" "):
                mh.style_issue(token.location,
                               "comment body must be separated with "
                               "whitespace from the starting %s" %
                               comment_char)
                token.raw_text = (comment_char * (len(token.raw_text) -
                                                  len(comment_body))
                                  + " "
                                  + comment_body)


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
        tb = Token_Buffer(lexer)
    except Error:
        # If there are lex errors, we can stop here
        return

    # Stange 2. Look at raw token stream for some of the more basic
    # rules.

    stage_2_analysis(cfg, tb)

    # Re-write the file, with issues fixed

    if autofix:
        with open(filename, "w", encoding=encoding) as fd:
            tb.replay(fd)


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
    ap.add_argument("--fix",
                    action="store_true",
                    default=False,
                    help="Automatically fix issues where the fix is obvious")
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
    # mh.sort_messages = False

    for item in options.files:
        if os.path.isdir(item):
            config.register_tree(os.path.abspath(item))
        elif os.path.isfile(item):
            config.register_tree(os.path.dirname(os.path.abspath(item)))
    config.build_config_tree(options)

    for item in options.files:
        if os.path.isdir(item):
            for path, _, files in os.walk(item):
                for f in files:
                    if f.endswith(".m"):
                        analyze(os.path.join(path, f), options.fix)
        else:
            analyze(item, options.fix)

    mh.print_summary_and_exit()


if __name__ == "__main__":
    main()
