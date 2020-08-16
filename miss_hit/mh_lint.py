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
##  free software: you can redistribute it and/or modify                    ##
##  it under the terms of the GNU Affero General Public License as          ##
##  published by the Free Software Foundation, either version 3 of the      ##
##  License, or (at your option) any later version.                         ##
##                                                                          ##
##  MISS_HIT is distributed in the hope that it will be useful,             ##
##  but WITHOUT ANY WARRANTY; without even the implied warranty of          ##
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           ##
##  GNU Afferto General Public License for more details.                    ##
##                                                                          ##
##  You should have received a copy of the GNU Affero General Public        ##
##  License along with MISS_HIT. If not, see                                ##
##  <http://www.gnu.org/licenses/>.                                         ##
##                                                                          ##
##############################################################################

from miss_hit_core import command_line
from miss_hit_core import work_package
from miss_hit_core.errors import Message_Handler, Error
from miss_hit_core.m_lexer import MATLAB_Lexer
from miss_hit_core.m_parser import MATLAB_Parser


class MH_Lint_Result(work_package.Result):
    def __init__(self, wp):
        super().__init__(wp, True)


class MH_Lint(command_line.MISS_HIT_Back_End):
    def __init__(self, _):
        super().__init__("MH Lint")

    @classmethod
    def process_wp(cls, wp):
        # Create lexer
        lexer = MATLAB_Lexer(wp.mh,
                             wp.get_content(),
                             wp.filename,
                             wp.blockname)
        if wp.cfg.octave:
            lexer.set_octave_mode()
        if not wp.cfg.pragmas:
            lexer.process_pragmas = False
        if len(lexer.text.strip()) == 0:
            return MH_Lint_Result(wp)

        # Create parse tree
        try:
            parser = MATLAB_Parser(wp.mh, lexer, wp.cfg)
            parser.parse_file()
        except Error:
            return MH_Lint_Result(wp)

        return MH_Lint_Result(wp)


def main_handler():
    clp = command_line.create_basic_clp()
    options = command_line.parse_args(clp)

    mh = Message_Handler("lint")
    mh.show_context = not options.brief
    mh.show_style   = False
    mh.show_checks  = True
    mh.autofix      = False

    lint_backend = MH_Lint(options)
    command_line.execute(mh, options, {}, lint_backend)


def main():
    command_line.ice_handler(main_handler)


if __name__ == "__main__":
    main()
