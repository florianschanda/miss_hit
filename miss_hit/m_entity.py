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

from miss_hit_core.m_entity_root import Entity
from miss_hit_core.m_ast import *


##############################################################################
# Symbol table
##############################################################################

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

    def dump(self, filename=None):
        title = "Symbol table"
        if filename:
            title += " for %s" % filename
        title += " with %u active scopes:" % len(self.names)
        print(title)
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


class Package_Entity(Entity):
    # Packages are directories starting with a '+'. There are some
    # fine points here: firstly, can split this over multiple
    # directories (i.e. if a and b are on your path, and both contain
    # +foo, then this is not an error). Secondly, any directory can
    # also contain a private directory: the contents are available in
    # that parent directory only, and do not extend over the entire
    # package.
    #
    # Hence our packages (which are entities) are actually collections
    # of package directories (which are not entities).
    def __init__(self, name):
        super().__init__(name               = name,
                         externally_visible = True)

        self.directories = []
        self.class_directories = []
        self.children = {}

    def add_directory(self, pkgdir):
        assert isinstance(pkgdir, Package_Directory)
        self.directories.append(pkgdir)

    def add_class_directory(self, clsdir):
        assert isinstance(clsdir, Class_Directory)
        self.class_directories.append(clsdir)

    def add_child_package(self, pkg):
        assert isinstance(pkg, Package_Entity)

        if pkg.name in self.children:
            raise ICE("NIY: merging packages")

        else:
            self.children[pkg.name] = pkg


class Directory:
    def __init__(self, dirname):
        assert isinstance(dirname, str)
        self.dirname = dirname

        self.private_directory = None

    def set_private_directory(self, prvdir):
        assert isinstance(prvdir, Private_Directory)
        if self.private_directory is not None:
            raise ICE("set duplicate private directory")
        self.private_directory = prvdir

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__,
                           self.dirname)


class Package_Directory(Directory):
    pass


class Global_Scope(Package_Directory):
    pass


class Class_Directory(Directory):
    pass


class Private_Directory(Directory):
    def set_private_directory(self, prvdir):
        raise ICE("set private directory on private directory")


##############################################################################
# Entities
##############################################################################

class Function_Entity(Entity):
    def __init__(self, n_fsig):
        assert isinstance(n_fsig, Function_Signature)
        super().__init__(name = str(n_fsig.n_name))

        self.n_definition = None
        # The actual function body.

        self.n_declaration = n_fsig
        # The original declaration. While usually n_definition.n_sig
        # is n_declaration, this is not true for separates. In this
        # case the decclaration refers to the signature in the main
        # class file, and the definition refers to the separate body.


class Class_Entity(Entity):
    def __init__(self, n_classdef):
        assert isinstance(n_classdef, Class_Definition)
        super().__init__(name               = str(n_classdef.n_name),
                         externally_visible = True)
        # Note: it is not legal to have a local or private class.

        self.n_definition = n_classdef
        self.n_definition.entity = self
        # The actual definition

        self.el_super = []
        # Entity list of super-classes

    def dump(self):
        print("Class Entity (%s)" % self.name)
        print("  definition: %s" % self.n_definition.loc())
