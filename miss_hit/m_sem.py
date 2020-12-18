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

from miss_hit_core.m_ast import *
from miss_hit_core.errors import Message_Handler, ICE

from miss_hit.m_entity import *


def treewalk(n_root, function):
    assert isinstance(n_root, Node)

    class Visitor(AST_Visitor):
        def visit(self, node, n_parent, relation):
            function(node)

    n_root.visit(None, Visitor(), "Root")


class Scope:
    # https://www.mathworks.com/help/matlab/matlab_prog/function-precedence-order.html
    #
    # Note that names (for functions) are resolved in this order:
    #
    #  1. Variable in the current workspace
    #  2. Imported name
    #  3. Nested functions in the current function
    #  4. Local function in the current file
    #  5. Wildcard imported name
    #  6. Private function (functions in a directory 'private' relative
    #     to the current file)
    #  7. Object functions (todo: unclear. are these methods?)
    #  8. Class constructors in @ directories (i.e. @foo/foo.m)
    #  9. Loaded simulink models (todo: unclear what this means)
    # 10. Functions in the current directory
    # 11. Functions on path, based on the path ordering
    #
    # Since calling Simulink models in a context that is not the
    # MATLAB command prompt, we can ignore (9).
    #
    # The 'current directory' (10) will be somwehat irrelevant as
    # well, since a MISS_HIT entry-point should produce a sensible
    # path.
    #
    # If there is a conflict within the same directory, it is resolved
    # using this order of preference:
    #
    # 1. Built-in function
    # 2. MEX function
    # 3. Simulink models that are not loaded (preferring slx over mdl)
    # 4. Stateflow chart with a .sfx extension
    # 5. App file (.mlapp) created by the App Designer
    # 6. mlx files
    # 7. p files
    # 8. m files
    #
    # Since the context of MISS_HIT is industrial, and generally
    # assuming this are sane; any confliuct here will just trigger an
    # error.
    #
    # Further, only (1) and (8) will be considered, since those are
    # the only sane things we can analyze.
    #
    # Also see:
    # https://www.mathworks.com/help/matlab/matlab_oop/scoping-classes-with-packages.html
    def __init__(self):
        self.names = [{}]

    def dump(self):
        print("Symbol table with %u active scopes:" % len(self.names))
        for level, names in enumerate(self.names, 1):
            print("=== Level %u ===" % level)
            for name in sorted(names):
                e_sym = names[name]
                e_sym.dump()

    def push(self):
        self.names.append({})

    def pop(self):
        if self.names:
            self.names.pop()
        else:
            raise ICE("tried to pop empty scope stack")

    def register(self, mh, entity):
        assert isinstance(mh, Message_Handler)
        assert isinstance(entity, Entity)

        if entity.name in self.names[-1]:
            # TODO: improve error message
            mh.error(entity.loc(),
                     "duplicate definition")

        else:
            self.names[-1][entity.name] = entity

    def lookup_str(self, name):
        assert isinstance(name, str)
        for layer in reversed(self.names):
            if name in layer:
                return layer[name]
        return None

    def lookup_token(self, mh, token, fatal=True):
        assert isinstance(mh, Message_Handler)
        assert isinstance(token, MATLAB_Token)
        assert token.kind in ("IDENTIFIER", "KEYWORD")
        assert isinstance(fatal, bool)

        entity = self.lookup_str(token.value)

        if fatal and entity is None:
            mh.error(token.location,
                     "unknown name")

        return entity

    def lookup_identifier(self, mh, n_ident, fatal=True):
        assert isinstance(mh, Message_Handler)
        assert isinstance(n_ident, Identifier)
        assert isinstance(fatal, bool)

        return self.lookup_token(n_ident.t_ident, fatal)

    def import_visible_names(self, other):
        assert isinstance(other, Scope)

        # Very important assumption here is that any duplicate
        # definitions have already been checked.

        for e_sym in other.names[-1].values():
            if not e_sym.is_externally_visible:
                continue
            if e_sym.name in self.names[-1]:
                raise ICE("attempted to import already already known "
                          "symbol %s" % e_sym.name)
            self.names[-1][e_sym.name] = e_sym


class Semantic_Analysis:
    def __init__(self, mh):
        assert isinstance(mh, Message_Handler)
        self.mh    = mh
        self.scope = Scope()

    def sem_compilation_unit(self, n_cu):
        assert isinstance(n_cu, Compilation_Unit)

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


def sem_pass1(mh, n_cu):
    assert isinstance(mh, Message_Handler)
    assert isinstance(n_cu, Compilation_Unit)

    rv = Semantic_Analysis(mh)
    rv.sem_compilation_unit(n_cu)

    return rv
