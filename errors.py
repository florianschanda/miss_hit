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

import m_lexer

class MISS_HIT_Error(Exception):
    def __init__(self, message):
        self.message = message

    def print_message(self):
        print(self.message)

class ICE(MISS_HIT_Error):
    def __init__(self, reason):
        super().__init__(reason)

    def print_message(self):
        print("ICE: %s" % self.message)

class Lex_Error(MISS_HIT_Error):
    def __init__(self, filename, message, context, line, col_start, col_end):
        super().__init__(message)
        assert isinstance(filename, str) and len(filename) > 0
        assert isinstance(context, str)
        assert isinstance(line, int) and line >= 0
        assert isinstance(col_start, int) and col_start >= 0
        assert isinstance(col_end, int) and col_end >= 0

        self.context   = context
        self.filename  = filename
        self.line      = line
        self.col_start = col_start
        self.col_end   = max(col_start, col_end)

    def print_message(self):
        print("In %s, line %u" % (self.filename, self.line))
        print("| " + self.context.replace("\t", " "))
        print("| " +
              (" " * self.col_start) +
              ("^" * (self.col_end - self.col_start + 1)) +
              " lex error: " + self.message)

class Parse_Error(MISS_HIT_Error):
    def __init__(self, token, message):
        assert isinstance(token, m_lexer.MATLAB_Token)
        super().__init__(message)
        self.token = token

    def print_message(self):
        self.token.print_message("error: %s" % self.message)
