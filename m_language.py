#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2019-2020, Florian Schanda                    ##
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

# Tokens for the MATLAB language
TOKEN_KINDS = frozenset([
    "NEWLINE",
    "CONTINUATION",
    "COMMENT",
    "IDENTIFIER",
    "NUMBER",
    "CARRAY",          # 'foo' character array
    "STRING",          # "foo" string class literal
    "KEYWORD",         # see below
    "OPERATOR",        # see docs/internal/matlab_operators.txt
    "COMMA",           # ,
    "SEMICOLON",       # ;
    "COLON",           # :
    "BRA", "KET",      # ( )
    "C_BRA", "C_KET",  # { }
    "M_BRA", "M_KET",  # [ ] for matrices
    "A_BRA", "A_KET",  # [ ] for assignment targets
    "ASSIGNMENT",      # =
    "SELECTION",       # .
    "AT",              # @
    "BANG",            # !
    "METACLASS",       # ?
    "NVP_DELEGATE",    # .? (name value pair delegation)
    "ANNOTATION",      # miss_hit annotation
])

# As of MATLAB 2019b
# See: https://www.mathworks.com/help/matlab/ref/iskeyword.html
#
# We have taken the liberty to make "import" a keyword, since that
# simplifies parsing quite a bit. This does mean that you can't have
# variables named "import".
#
# There are a few more keywords, but they are not always keywords. The
# lexer also sometimes emits properties, arguments, methods, events,
# and enumeration as keywords, depending on context.
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

    # These really should be keywords but are not
    'import',
])

# The annotation language defines more keywords
ANNOTATION_KEYWORDS = KEYWORDS | frozenset([
    'pragma',
])
