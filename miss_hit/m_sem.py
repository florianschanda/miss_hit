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

from miss_hit_core.m_ast import *
from miss_hit_core.errors import Message_Handler, ICE
from miss_hit_core.cfg_ast import Library_Declaration, Entrypoint_Declaration
from miss_hit_core import cfg_tree

from miss_hit.m_entity import *


def treewalk(n_root, function):
    assert isinstance(n_root, Node)

    class Visitor(AST_Visitor):
        def visit(self, node, n_parent, relation):
            function(node)

    n_root.visit(None, Visitor(), "Root")


class Semantic_Analysis_Pass_1:
    def __init__(self, mh):
        assert isinstance(mh, Message_Handler)
        self.mh    = mh
        self.scope = Scope()
        self.pkg   = []

    def sem_compilation_unit(self, n_cu):
        assert isinstance(n_cu, Compilation_Unit)

        n_cu.scope = self.scope

        if isinstance(n_cu, Class_File):
            self.sem_class_file(n_cu)
        elif isinstance(n_cu, Function_File):
            pass
        elif isinstance(n_cu, Script_File):
            pass
        else:
            raise ICE("unexpected compilation unit type %s" %
                      n_cu.__class__.__name__)

    def sem_class_file(self, n_cf):
        assert isinstance(n_cf, Class_File)

        e_cls = Class_Entity(n_cf.n_classdef)
        self.scope.register(self.mh, e_cls)


def sem_pass_1(mh, entrypoint, n_cu):
    assert isinstance(mh, Message_Handler)
    assert isinstance(n_cu, Compilation_Unit)
    assert isinstance(entrypoint, (Library_Declaration,
                                   Entrypoint_Declaration)) or \
        entrypoint is None

    rv = Semantic_Analysis_Pass_1(mh)
    rv.sem_compilation_unit(n_cu)

    item = os.path.normpath(n_cu.dirname)
    if entrypoint:
        best_match = None
        for path in cfg_tree.get_source_path(entrypoint):
            search_item = os.path.normpath(path)
            if item.startswith(search_item):
                if best_match is None or len(best_match) < len(search_item):
                    best_match = search_item
        if best_match is None:
            raise ICE("could not find %s on path" % n_cu.dirname)
        packages = item[len(best_match) + 1:]
        if os.sep != "/":
            packages = packages.replace(os.sep, "/")
        if packages:
            packages = packages.split("/")
            rv.pkg = packages
        else:
            packages = []

        # We have an empty list, or a list of + directories, followed
        # by at most one @ directory, followed optionally by a private
        # directory.
        current_dir = best_match
        sequence = "package"

        for item in packages:
            current_dir = os.path.join(current_dir, item)
            if item.startswith("+"):
                if sequence == "package":
                    pass
                else:
                    mh.check(n_cu.loc(),
                             "cannot nest package inside a %s" % sequence)
                    return None

            elif item.startswith("@"):
                if sequence == "package":
                    sequence = "class directory"

                else:
                    mh.check(n_cu.loc(),
                             "cannot nest class directory inside a %s" %
                             sequence)
                    return None

            elif item == "private":
                if sequence in ("package", "class directory"):
                    sequence = "private directory"

                else:
                    mh.check(n_cu.loc(),
                             "cannot private directory inside a %s" %
                             sequence)
                    return None

            else:
                mh.check(n_cu.loc(),
                         "is not on path and cannot be accessed" %
                         sequence)
                return None

    return rv
