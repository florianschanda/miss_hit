#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2020-2021, Florian Schanda                    ##
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

import os

from miss_hit_core import command_line
from miss_hit_core import work_package
from miss_hit_core import cfg_tree
from miss_hit_core.m_ast import *
from miss_hit_core.errors import (Error,
                                  Message_Handler,
                                  HTML_Message_Handler,
                                  JSON_Message_Handler)
from miss_hit_core.m_lexer import MATLAB_Lexer
from miss_hit_core.m_parser import MATLAB_Parser

from miss_hit.m_sem import sem_pass_1


class Stage_1_Linting(AST_Visitor):
    """ Checks which do not require semantic analysis """
    def __init__(self, mh):
        self.mh = mh

    def visit(self, node, n_parent, relation):
        if isinstance(node, Compilation_Unit):
            self.check_compilation_unit(node)

    def check_compilation_unit(self, n_cu):
        assert isinstance(n_cu, Compilation_Unit)

        if isinstance(n_cu, Function_File):
            self.check_filename(file_name = n_cu.name,
                                kind      = "function",
                                ent_name  = n_cu.l_functions[0].n_sig.n_name)
        elif isinstance(n_cu, Class_File):
            self.check_filename(file_name = n_cu.name,
                                kind      = "class",
                                ent_name  = n_cu.n_classdef.n_name)

    def check_filename(self, file_name, kind, ent_name):
        assert isinstance(file_name, str)
        assert isinstance(ent_name, Name) and ent_name.is_simple_dotted_name()

        base_filename, ext = os.path.splitext(file_name)

        if ext != ".m":
            # This check is not applicable for MATLAB embedded in
            # Simulink models
            pass
        elif base_filename != str(ent_name):
            self.mh.check(ent_name.loc(),
                          "%s name does not match the filename %s" %
                          (kind, base_filename),
                          "low")


class MH_Lint_Result(work_package.Result):
    def __init__(self, wp, sem=None):
        super().__init__(wp, True)
        self.sem = sem


class MH_Lint(command_line.MISS_HIT_Back_End):
    def __init__(self, options):
        super().__init__("MH Lint")
        self.perform_sem = options.entry_point is not None
        self.debug_show_st = options.debug_show_global_symbol_table

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
            n_cu = parser.parse_file()
        except Error:
            return MH_Lint_Result(wp)

        # Initial checks
        n_cu.visit(None, Stage_1_Linting(wp.mh), "Root")

        # First pass of semantic analysis
        entrypoint = cfg_tree.get_entry_point(wp.options.entry_point)
        sem = sem_pass_1(wp.mh, entrypoint, n_cu)

        return MH_Lint_Result(wp, sem)

    def process_result(self, result):
        if not self.perform_sem:
            return
        if not isinstance(result, MH_Lint_Result):
            return
        if result.sem is None:
            return

        if self.debug_show_st:
            result.sem.scope.dump(result.wp.filename)

    def post_process(self):
        pass


def main_handler():
    clp = command_line.create_basic_clp()

    # Extra output options
    clp["output_options"].add_argument(
        "--html",
        default=None,
        help="Write report to given file as HTML")
    clp["output_options"].add_argument(
        "--json",
        default=None,
        help="Produce JSON report")

    # Extra debug options
    clp["debug_options"].add_argument(
        "--debug-show-global-symbol-table",
        default=False,
        action="store_true",
        help="Show global symbol table")

    options = command_line.parse_args(clp)

    if options.html:
        if options.json:
            clp["ap"].error("Cannot produce JSON and HTML at the same time")
        if os.path.exists(options.html) and not os.path.isfile(options.html):
            clp["ap"].error("Cannot write to %s: it is not a file" %
                            options.html)
        mh = HTML_Message_Handler("lint", options.html)
    elif options.json:
        if os.path.exists(options.json) and not os.path.isfile(options.json):
            clp["ap"].error("Cannot write to %s: it is not a file" %
                            options.json)
        mh = JSON_Message_Handler("lint", options.json)
    else:
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
