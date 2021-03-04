#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2021, Florian Schanda                         ##
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
from miss_hit_core import cfg_tree
from miss_hit_core.m_ast import *
from miss_hit_core.errors import Error, Message_Handler
from miss_hit_core.m_lexer import MATLAB_Lexer, Token_Buffer
from miss_hit_core.m_parser import MATLAB_Parser


class MH_Copyright_Result(work_package.Result):
    def __init__(self, wp, processed=False):
        super().__init__(wp, processed)


class MH_Copyright(command_line.MISS_HIT_Back_End):
    def __init__(self, options):
        super().__init__("MH Copyright")

    @classmethod
    def process_wp(cls, wp):
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
            return MH_Copyright_Result(wp)

        # Fix tabs, this is required for autofixing
        lexer.correct_tabs(wp.cfg.style_config["tab_width"])

        # Create tokenbuffer
        try:
            tbuf = Token_Buffer(lexer, wp.cfg)
        except Error:
            # If there are lex errors, we can stop here
            return MH_Copyright_Result(wp)

        # Create parse tree
        try:
            parser = MATLAB_Parser(wp.mh, tbuf, wp.cfg)
            parse_tree = parser.parse_file()
        except Error:
            return MH_Copyright_Result(wp)

        # TODO: Fix/modify/update copyright notices
        pass

        # Return results
        return MH_Copyright_Result(wp, True)


def main_handler():
    clp = command_line.create_basic_clp()

    clp["ap"].add_argument("--process-slx",
                           action="store_true",
                           default=False,
                           help=("Update copyright notices inside Simulink"
                                 " models. This option is temporary, and"
                                 " will be removed in future once the"
                                 " feature is good enough to be enabled"
                                 " by default."))

    options = command_line.parse_args(clp)

    mh = Message_Handler("copyright")

    mh.show_context = not options.brief
    mh.show_style   = False
    mh.show_checks  = False
    mh.autofix      = True

    copyright_backend = MH_Copyright(options)
    command_line.execute(mh, options, {},
                         copyright_backend,
                         options.process_slx)


def main():
    command_line.ice_handler(main_handler)


if __name__ == "__main__":
    main()
