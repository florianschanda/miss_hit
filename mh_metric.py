#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2020, Florian Schanda                         ##
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

# This is a code metric tool. It will implement popular and common
# metrics like path count or cyclomatic complexity.

import os

import command_line

from m_lexer import MATLAB_Lexer, Token_Buffer
from errors import Location, Error, ICE, Message_Handler, HTML_Message_Handler
import config
import config_files
from m_parser import MATLAB_Parser


def main():
    clp = command_line.create_basic_clp()
    options = command_line.parse_args(clp)

    mh = Message_Handler()

    mh.show_context = not options.brief
    mh.show_style   = False
    mh.autofix      = False

    command_line.read_config(mh, options)

    for item in options.files:
        if os.path.isdir(item):
            for path, dirs, files in os.walk(item):
                dirs.sort()
                for f in sorted(files):
                    if f.endswith(".m"):
                        pass
        else:
            pass

    mh.summary_and_exit()


if __name__ == "__main__":
    command_line.ice_handler(main)
