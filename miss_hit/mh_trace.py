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

import functools
import operator
import json

from miss_hit_core import command_line
from miss_hit_core import work_package
from miss_hit_core.m_ast import *
from miss_hit_core.errors import (Error,
                                  Message_Handler)
from miss_hit_core.m_lexer import MATLAB_Lexer
from miss_hit_core.m_parser import MATLAB_Parser


class MH_Trace_Result(work_package.Result):
    def __init__(self, wp, tracing=None):
        super().__init__(wp, True)
        self.tracing = tracing


class Function_Visitor(AST_Visitor):
    def __init__(self, mh, cu):
        assert isinstance(mh, Message_Handler)
        assert isinstance(cu, Compilation_Unit)

        self.tag_stack = []
        self.mh = mh
        self.tracing = {}
        self.name_prefix = cu.get_name_prefix()

    def get_test_tags(self, node):
        n_tags = node.get_attribute("TestTags")
        rv = set()

        if n_tags is None:
            return rv

        if not isinstance(n_tags.n_value, (Cell_Expression,
                                           Matrix_Expression)):
            self.mh.error(n_tags.n_value.loc(),
                          "TestTags value must be a cell or matrix",
                          fatal=False)
            return rv

        n_row_list = n_tags.n_value.n_content
        if len(n_row_list.l_items) != 1:
            self.mh.error(n_tags.n_value.loc(),
                          "TestTags value must only contain precisely"
                          " 1 row",
                          fatal=False)
            return rv

        for n_tag in n_row_list.l_items[0].l_items:
            if isinstance(n_tag, (Char_Array_Literal,
                                  String_Literal)):
                rv.add(n_tag.t_string.value)
            else:
                self.mh.error(n_tag.loc(),
                              "TestTags value must be a string or"
                              " carray literal",
                              fatal=False)

        return rv

    def visit(self, node, n_parent, relation):
        # Deal with the tag stack first
        if isinstance(node, Function_Definition):
            self.tag_stack.append(set())
        elif isinstance(node, Class_Definition):
            self.tag_stack.append(self.get_test_tags(node))
        elif isinstance(node, Compilation_Unit):
            self.tag_stack.append(set())
        elif isinstance(node, Special_Block) and node.kind() == "methods":
            self.tag_stack.append(self.get_test_tags(node))

        # Amend current tag stack if we get a tag pragma
        if isinstance(node, Tag_Pragma):
            self.tag_stack[-1] |= node.get_tags()

    def visit_end(self, node, n_parent, relation):
        # Create entry for tracing
        if isinstance(node, Function_Definition):
            name = self.name_prefix + node.get_local_name()
            self.tracing[name] = {
                "source": node.loc().to_json(detailed=False),
                "tags"  : sorted(functools.reduce(operator.or_,
                                                  self.tag_stack,
                                                  set()))
            }

        if isinstance(node, (Definition,
                             Compilation_Unit)):
            self.tag_stack.pop()
        elif isinstance(node, Special_Block) and node.kind() == "methods":
            self.tag_stack.pop()


class MH_Trace(command_line.MISS_HIT_Back_End):
    def __init__(self, options):
        super().__init__("MH Trace")
        self.tracing = {}
        self.options = options

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
            return MH_Trace_Result(wp)

        # Create parse tree
        try:
            parser = MATLAB_Parser(wp.mh, lexer, wp.cfg)
            n_cu = parser.parse_file()
        except Error:
            return MH_Trace_Result(wp)

        visitor = Function_Visitor(wp.mh, n_cu)
        n_cu.visit(None, visitor, "Root")

        # Return results
        return MH_Trace_Result(wp, visitor.tracing)

    def process_result(self, result):
        if result.tracing:
            self.tracing.update(result.tracing)

    def post_process(self):
        if self.options.by_tag:
            out = {}
            for unitname in sorted(self.tracing):
                source = self.tracing[unitname]["source"]
                tags   = self.tracing[unitname]["tags"]
                for tag in tags:
                    if tag not in out:
                        out[tag] = []
                    out[tag].append({"name"   : unitname,
                                     "source" : source})
        else:
            out = self.tracing

        with open(self.options.json, "w") as fd:
            json.dump(out, fd, indent=4, sort_keys=True)


def main_handler():
    clp = command_line.create_basic_clp()

    clp["output_options"].add_argument(
        "--json",
        default="mh_trace.json",
        help="name of the JSON report (by default mh_trace.json)")
    clp["output_options"].add_argument(
        "--by-tag",
        action="store_true",
        default=False,
        help=("group tracing information by tag; by default we group by"
              " unit name first"))

    options = command_line.parse_args(clp)

    mh = Message_Handler("trace")

    mh.show_context = not options.brief
    mh.show_style   = False
    mh.show_checks  = False
    mh.autofix      = False

    trace_backend = MH_Trace(options)
    command_line.execute(mh, options, {}, trace_backend,
                         process_tests=True)


def main():
    command_line.ice_handler(main_handler)


if __name__ == "__main__":
    main()
