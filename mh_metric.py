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

from m_lexer import MATLAB_Lexer
from errors import Location, Error, ICE, Message_Handler
import config_files
from m_parser import MATLAB_Parser

# pylint: disable=wildcard-import,unused-wildcard-import
from m_ast import *
# pylint: enable=wildcard-import,unused-wildcard-import


def collect_metrics(args):
    mh, filename, _ = args
    assert isinstance(filename, str)

    cfg = config_files.get_config(filename)
    metrics = {filename: {"errors" : False,
                          "metrics": {},
                          "functions" : {}}}

    if not cfg["enable"]:
        mh.register_exclusion(filename)
        return False, filename, mh, metrics

    mh.register_file(filename)

    # Do some file-based sanity checking

    try:
        if not os.path.exists(filename):
            mh.error(Location(filename), "file does not exist")
        if not os.path.isfile(filename):
            mh.error(Location(filename), "is not a file")
    except Error:
        metrics[filename]["errors"] = True
        return True, filename, mh, metrics

    # Create lexer

    try:
        lexer = MATLAB_Lexer(mh, filename, encoding="cp1252")
    except UnicodeDecodeError:
        lexer = MATLAB_Lexer(mh, filename, encoding="utf8")
    if cfg["octave"]:
        lexer.set_octave_mode()

    # We're dealing with an empty file here. Lets just not do anything

    if len(lexer.text.strip()) == 0:
        return True, filename, mh, metrics

    # File metrics

    metrics[filename]["metrics"] = {
        "lines" : len(lexer.context_line),
    }

    # Create parse tree

    try:
        parser = MATLAB_Parser(mh, lexer, cfg)
        parse_tree = parser.parse_file()
    except Error:
        metrics[filename]["errors"] = True
        return True, filename, mh, metrics

    # Collect function metrics

    metrics[filename]["functions"] = get_function_metrics(parse_tree)

    # Return results

    return True, filename, mh, metrics


def npath(node):
    assert isinstance(node, (Sequence_Of_Statements,
                             Statement))

    if isinstance(node, Sequence_Of_Statements):
        paths = 1
        for n_statement in node.l_statements:
            if isinstance(n_statement, (If_Statement,
                                        For_Loop_Statement,
                                        Switch_Statement,
                                        Try_Statement,
                                        While_Statement)):
                paths *= npath(n_statement)
        return paths

    elif isinstance(node, If_Statement):
        paths = 0
        for n_action in node.l_actions:
            paths += npath(n_action.n_body)
        if not node.has_else:
            paths += 1

        return paths

    elif isinstance(node, Switch_Statement):
        paths = 0
        for n_action in node.l_actions:
            paths += npath(n_action.n_body)
        if not node.has_otherwise:
            paths += 1

        return paths

    elif isinstance(node, (For_Loop_Statement, While_Statement)):
        return 1 + npath(node.n_body)

    elif isinstance(node, Try_Statement):
        return npath(node.n_body) * 2

    else:
        raise ICE("unexpected node")


def get_function_metrics(tree):
    assert isinstance(tree, Compilation_Unit)

    metrics = {}

    def process_function(n_fdef, naming_stack):
        assert isinstance(n_fdef, Function_Definition)

        # We need a unique name for the function for this file.
        name = "::".join(map(str, naming_stack + [n_fdef.n_sig.n_name]))

        metrics[name] = {
            "npath" : npath(n_fdef.n_body),
        }

    class Function_Visitor(AST_Visitor):
        def __init__(self):
            self.name_stack = []

        def visit(self, node, n_parent, relation):
            if isinstance(node, Function_Definition):
                process_function(node, self.name_stack)
                self.name_stack.append(node.n_sig.n_name)
            elif isinstance(node, Class_Definition):
                self.name_stack.append(node.n_name)

        def visit_end(self, node, n_parent, relation):
            if isinstance(node, Definition):
                self.name_stack.pop()

    tree.visit(None, Function_Visitor(), "Root")
    return metrics


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
                if path == ".":
                    path = ""
                dirs.sort()
                for f in sorted(files):
                    if f.endswith(".m"):
                        work_list.append((blank_mh(),
                                          os.path.join(path, f),
                                          options))
        else:
            work_list.append((blank_mh(), item, options))

    all_metrics = {}
    # file -> { metrics -> {}
    #           functions -> {name -> {}} }

    if options.single:
        for processed, filename, result, metrics in map(collect_metrics,
                                                        work_list):
            mh.integrate(result)
            if processed:
                mh.finalize_file(filename)
                all_metrics.update(metrics)

    else:
        pool = multiprocessing.Pool()
        for processed, filename, result, metrics in pool.imap(collect_metrics,
                                                              work_list,
                                                              5):
            mh.integrate(result)
            if processed:
                mh.finalize_file(filename)
                all_metrics.update(metrics)

    # Print metrics to stdout for now
    for filename in sorted(all_metrics):
        metrics = all_metrics[filename]
        print("Code metrics for file %s:" % filename)
        if metrics["errors"]:
            print("  Contains syntax or semantics errors!")
        print("  Lines: %u" % metrics["metrics"]["lines"])
        for function in sorted(metrics["functions"]):
            f_metrics = metrics["functions"][function]
            print("  Code metrics for function %s:" % function)
            print("    Path count: %u" % f_metrics["npath"])

    mh.summary_and_exit()


if __name__ == "__main__":
    command_line.ice_handler(main)
