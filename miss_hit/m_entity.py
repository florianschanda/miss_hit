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

from miss_hit_core.m_entity_root import Entity
from miss_hit_core.m_ast import *


class Function_Entity(Entity):
    pass


class Class_Entity(Entity):
    def __init__(self, n_classdef):
        assert isinstance(n_classdef, Class_Definition)
        super().__init__(name               = str(n_classdef.n_name),
                         externally_visible = True)

        self.n_definition = n_classdef
        self.n_definition.entity = self
        # The actual definition

        self.el_super = []
        # Entity list of super-classes

    def dump(self):
        print("Class Entity (%s)" % self.name)
        print("  definition: %s" % self.n_definition.loc())
