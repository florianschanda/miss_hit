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

class ICE(Exception):
    def __init__(self, reason):
        self.reason = reason

class Anonymous_Parse_Error(Exception):
    def __init__(self, filename, line, message):
        assert isinstance(filename, str) and len(filename) > 0
        assert isinstance(line, int) and line >= 0

        self.filename = filename
        self.line     = line
        self.message  = message

class Parse_Error(Anonymous_Parse_Error):
    def __init__(self, token, message):
        assert isinstance(token, m_lexer.MATLAB_Token)
        super().__init__(token.filename,
                         token.line,
                         message)
        self.token = token
