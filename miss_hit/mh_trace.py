#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2021-2022, Florian Schanda                    ##
##              Copyright (C) 2023,      BMW AG                             ##
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
from miss_hit_core import s_ast

from miss_hit_core.m_ast import *
from miss_hit_core.errors import (Error,
                                  Message_Handler)
from miss_hit_core.m_lexer import MATLAB_Lexer
from miss_hit_core.m_parser import MATLAB_Parser
from miss_hit_core.cfg_tree import get_enclosing_ep
from miss_hit_core.cfg_ast import Project_Directive


class MH_Trace_Result(work_package.Result):
    def __init__(self, wp, imp_items=None, act_items=None):
        super().__init__(wp, True)
        self.imp_items = imp_items
        self.act_items = act_items


class Function_Visitor(AST_Visitor):
    def __init__(self, in_test_dir, mh, cu, ep):
        assert isinstance(in_test_dir, bool)
        assert isinstance(mh, Message_Handler)
        assert isinstance(cu, Compilation_Unit)
        assert ep is None or isinstance(ep, Project_Directive)

        self.in_test_dir = in_test_dir
        self.tag_stack = []
        self.no_tracing_stack = []
        self.mh = mh
        self.imp_items = []
        self.act_items = []
        self.name_prefix = cu.get_name_prefix()
        self.in_test_block = False
        if ep is None:
            self.is_shared = False
        else:
            self.is_shared = ep.shared

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
            self.no_tracing_stack.append(False)
        elif isinstance(node, Class_Definition):
            self.tag_stack.append(self.get_test_tags(node))
            self.no_tracing_stack.append(False)
        elif isinstance(node, Compilation_Unit):
            self.tag_stack.append(set())
            self.no_tracing_stack.append(False)
        elif isinstance(node, Special_Block) and node.kind() == "methods":
            self.tag_stack.append(self.get_test_tags(node))
            self.no_tracing_stack.append(False)
            self.in_test_block = node.get_attribute("Test") is not None

        elif isinstance(node, Tag_Pragma):
            # Amend current tag stack if we get a tag pragma
            self.tag_stack[-1] |= node.get_tags()

        elif isinstance(node, No_Tracing_Pragma):
            # Make a note of this no_tracing pragma
            self.no_tracing_stack[-1] = True

    def visit_end(self, node, n_parent, relation):
        # Create entry for tracing
        if isinstance(node, Function_Definition) and \
           not any(self.no_tracing_stack):
            name = self.name_prefix + node.get_local_name()
            tag  = "matlab %s" % name
            location = node.loc()
            lobster_loc  = {"kind"   : "file",
                            "file"   : location.filename,
                            "line"   : location.line,
                            "column" : location.col_start}
            all_tags = sorted(functools.reduce(operator.or_,
                                               self.tag_stack,
                                               set()))
            item = {"tag"         : tag,
                    "location"    : lobster_loc,
                    "name"        : node.get_local_name(),
                    "refs"        : ["req %s" % tag for tag in all_tags],
                    "just_up"     : [],
                    "just_down"   : [],
                    "just_global" : []}

            if self.in_test_block or self.in_test_dir:
                item["framework"] = "MATLAB"
                item["kind"]      = "Test"
                item["status"]    = None
                self.act_items.append(item)

            else:
                item["language"] = "MATLAB"
                item["kind"]     = "Function"
                item["shared"]   = self.is_shared
                self.imp_items.append(item)

        if isinstance(node, (Definition,
                             Compilation_Unit)):
            self.tag_stack.pop()
            self.no_tracing_stack.pop()

        elif isinstance(node, Special_Block) and node.kind() == "methods":
            self.tag_stack.pop()
            self.no_tracing_stack.pop()
            self.in_test_block = False


class Simulink_Walker:
    def __init__(self, in_test_dir, mh, n_root, ep):
        assert isinstance(n_root, s_ast.Container)
        assert ep is None or isinstance(ep, Project_Directive)

        self.in_test_dir = in_test_dir
        self.mh          = mh
        self.n_root      = n_root
        self.imp_items   = []
        self.act_items   = []
        if ep is None:
            self.is_shared = False
        else:
            self.is_shared = ep.shared

        self.naming_stack = [n_root.name]
        self.walk_container(self.n_root)

    def walk_container(self, n_container):
        self.walk_system(n_container.n_system)

    def walk_system(self, n_system):
        TRACE_PREFIX = "lobster-trace:"

        name = "/".join(self.naming_stack)
        tag  = "simulink %s" % name
        lobster_loc  = {"kind"   : "file",
                        "file"   : self.n_root.filename,
                        "line"   : None,
                        "column" : None}
        item = {"tag"         : tag,
                "location"    : lobster_loc,
                "name"        : name,
                "refs"        : [],
                "just_up"     : [],
                "just_down"   : [],
                "just_global" : []}

        for n_anno in n_system.d_annos.values():
            if n_anno.text.startswith(TRACE_PREFIX):
                item["refs"] += \
                    ["req %s" % x.strip()
                     for x in n_anno.text[len(TRACE_PREFIX):].split(",")]

        if self.in_test_dir:
            item["framework"] = "SIMULINK"
            item["kind"]      = "Test"
            item["status"]    = None
            self.act_items.append(item)
        else:
            item["language"] = "Simulink"
            item["kind"]     = "Block"
            item["shared"]   = self.is_shared
            self.imp_items.append(item)

        for n_block in n_system.d_blocks.values():
            if isinstance(n_block, s_ast.Sub_System):
                self.walk_subsystem(n_block)

    def walk_subsystem(self, n_subsystem):
        self.naming_stack.append(n_subsystem.name)
        self.walk_system(n_subsystem.n_system)
        self.naming_stack.pop()


class MH_Trace(command_line.MISS_HIT_Back_End):
    def __init__(self, options):
        super().__init__("MH Trace")
        self.imp_items = []
        self.act_items = []
        self.options   = options

    @classmethod
    def process_wp(cls, wp):
        # Create lexer
        lexer = MATLAB_Lexer(wp.cfg.language,
                             wp.mh,
                             wp.get_content(),
                             wp.filename,
                             wp.blockname)
        if not wp.cfg.pragmas:
            lexer.process_pragmas = False
        if len(lexer.text.strip()) == 0:
            return MH_Trace_Result(wp)

        # Create parse tree
        try:
            parser = MATLAB_Parser(wp.mh, lexer, wp.cfg)
            n_cu = parser.parse_file()
            n_ep = get_enclosing_ep(wp.filename)
        except Error:
            return MH_Trace_Result(wp)

        visitor = Function_Visitor(wp.in_test_dir, wp.mh, n_cu, n_ep)
        n_cu.visit(None, visitor, "Root")

        # Return results
        return MH_Trace_Result(wp, visitor.imp_items, visitor.act_items)

    @classmethod
    def process_simulink_wp(cls, wp):
        assert isinstance(wp, work_package.SIMULINK_File_WP)

        if wp.n_content is None:
            return MH_Trace_Result(wp)
        else:
            n_ep = get_enclosing_ep(wp.filename)
            walker = Simulink_Walker(wp.in_test_dir, wp.mh, wp.n_content, n_ep)
            return MH_Trace_Result(wp, walker.imp_items, walker.act_items)

    def process_result(self, result):
        if result.imp_items:
            self.imp_items += result.imp_items
        if result.act_items:
            self.act_items += result.act_items

    def post_process(self):
        if self.options.only_tagged_blocks:
            self.imp_items = list(filter(
                lambda x: x["language"] != "Simulink" or x["refs"],
                self.imp_items))
            self.act_items = list(filter(
                lambda x: x["framework"] != "Simulink" or x["refs"],
                self.act_items))

        with open(self.options.out_imp, "w", encoding="UTF-8") as fd:
            data = {"data"      : self.imp_items,
                    "generator" : "MH Trace",
                    "schema"    : "lobster-imp-trace",
                    "version"   : 3}
            json.dump(data, fd, indent=2, sort_keys=True)
            fd.write("\n")
        with open(self.options.out_act, "w", encoding="UTF-8") as fd:
            data = {"data"      : self.act_items,
                    "generator" : "MH Trace",
                    "schema"    : "lobster-act-trace",
                    "version"   : 3}
            json.dump(data, fd, indent=2, sort_keys=True)
            fd.write("\n")


def main_handler():
    clp = command_line.create_basic_clp()

    clp["output_options"].add_argument(
        "--out-imp",
        default="mh_imp_trace.lobster",
        help=("name of the implementation LOBSTER artefact"
              " (by default %(default)s)"))
    clp["output_options"].add_argument(
        "--out-act",
        default="mh_act_trace.lobster",
        help=("name of the activity LOBSTER artefact"
              " (by default %(default)s)"))
    clp["output_options"].add_argument(
        "--only-tagged-blocks",
        action="store_true",
        default=False,
        help="Only emit traces for Simulink blocks with at least one tag")

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
