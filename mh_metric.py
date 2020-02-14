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
import multiprocessing

import command_line

from m_lexer import MATLAB_Lexer, Token_Buffer
from errors import Location, Error, ICE, Message_Handler, HTML_Message_Handler
import config
import config_files
from m_parser import MATLAB_Parser


def collect_metrics(args):
    mh, filename, options = args
    assert isinstance(filename, str)

    cfg = config_files.get_config(filename)

    if not cfg["enable"]:
        mh.register_exclusion(filename)
        return False, filename, mh

    mh.register_file(filename)

    # Do some file-based sanity checking

    try:
        if not os.path.exists(filename):
            mh.error(Location(filename), "file does not exist")
        if not os.path.isfile(filename):
            mh.error(Location(filename), "is not a file")
    except Error:
        return True, filename, mh

    # Create lexer

    try:
        lexer = MATLAB_Lexer(mh, filename, encoding="cp1252")
    except UnicodeDecodeError:
        lexer = MATLAB_Lexer(mh, filename, encoding="utf8")
    if cfg["octave"]:
        lexer.set_octave_mode()

    # We're dealing with an empty file here. Lets just not do anything

    if len(lexer.text.strip()) == 0:
        return True, filename, mh

    # Create parse tree

    try:
        parser = MATLAB_Parser(mh, lexer, cfg)
        parse_tree = parser.parse_file()
    except Error:
        return True, filename, mh

    # Collect metrics

    pass

    # Emit messages

    return True, filename, mh


def main():
    clp = command_line.create_basic_clp()
    options = command_line.parse_args(clp)

    def blank_mh():
        mh = Message_Handler()
        mh.show_context = not options.brief
        mh.show_style   = False
        mh.autofix      = False
        return mh

    mh = blank_mh()

    command_line.read_config(mh, options)

    work_list = []
    for item in options.files:
        if os.path.isdir(item):
            for path, dirs, files in os.walk(item):
                dirs.sort()
                for f in sorted(files):
                    if f.endswith(".m"):
                        work_list.append((blank_mh(),
                                          os.path.join(path, f),
                                          options))
        else:
            work_list.append((blank_mh(), item, options))

    pool = multiprocessing.Pool()
    for processed, filename, result in pool.imap(collect_metrics,
                                                 work_list,
                                                 5):
        mh.integrate(result)
        if processed:
            mh.finalize_file(filename)

    # for processed, filename, result in map(collect_metrics,
    #                                        work_list):
    #     mh.integrate(result)
    #     if processed:
    #         mh.finalize_file(filename)

    mh.summary_and_exit()


if __name__ == "__main__":
    command_line.ice_handler(main)
