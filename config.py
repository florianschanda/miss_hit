#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
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

import os
from copy import deepcopy

from m_lexer import MATLAB_Lexer
from errors import mh, Error, Location

CONFIG_FILENAME = "miss_hit.cfg"

DEFAULT = {
    "file_length"      : 1000,
    "line_length"      : 80,
    "tab_width"        : 4,
    "copyright_entity" : set()
}

def find_config_file():
    """ Find config file for MISS_HIT by going up the directory tree """
    path = os.getcwd()
    while not os.path.isfile(os.path.join(path, CONFIG_FILENAME)):
        parent = os.path.dirname(path)
        if parent == path:
            return None
        path = parent

    path = os.path.normpath(os.path.join(os.path.relpath(path),
                                         CONFIG_FILENAME))
    return path

class Config_Parser:
    def __init__(self, config_file):
        self.filename = config_file
        self.lexer = MATLAB_Lexer(self.filename)
        self.ct = None
        self.nt = None
        self.next()

    def next(self):
        self.ct = self.nt
        self.nt = self.lexer.token()

        while self.nt:
            # Skip comments
            while self.nt and self.nt.kind == "COMMENT":
                self.nt = self.lexer.token()

            # Join new-lines
            if (self.nt and
                self.ct and
                self.nt.kind == "NEWLINE" and
                self.ct.kind == "NEWLINE"):
                self.nt = self.lexer.token()
            else:
                break

    def match(self, kind, value=None):
        self.next()
        if self.ct is None:
            mh.error(Location(self.lexer.filename),
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
        self.ct

    def parse_file(self):
        options = deepcopy(DEFAULT)

        while self.nt:
            if self.nt.kind == "NEWLINE":
                self.match("NEWLINE")
            else:
                self.match("IDENTIFIER")
                t_key = self.ct
                key = self.ct.value()
                self.match("COLON")

                if key not in options:
                    mh.error(t_key.location,
                             "unknown option %s" % key)
                elif isinstance(options[key], int):
                    self.match("NUMBER")
                    try:
                        value = int(self.ct.value())
                    except ValueError:
                        mh.error(self.ct.location,
                                 "%s option requires an integer" % key)
                elif isinstance(options[key], set):
                    self.match("STRING")
                    value = self.ct.value()

                if self.nt:
                    self.match("NEWLINE")
                else:
                    self.match_eof()

                if isinstance(options[key], set):
                    options[key].add(value)
                else:
                    options[key] = value

        return options

def load_config():
    cfg = deepcopy(DEFAULT)

    cfg_file = find_config_file()
    if cfg_file is None:
        return cfg

    try:
        p = Config_Parser(cfg_file)
        cfg = p.parse_file()
        # Now that we have parsed the file, we should remove it again
        # from the list of files known to the error handler
        mh.unregister_file(cfg_file)
    except Error:
        mh.print_summary_and_exit()

    return cfg
