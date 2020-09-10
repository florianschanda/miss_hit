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

# Simple helper for performing type inference. You start with all
# options, and then you can exclude specific classes trees or assert
# the option must be in a specific class tree.

import inspect
from copy import copy

from miss_hit_core import m_types
from miss_hit import graph


def build_masks():
    cls_graph = graph.Graph()
    nv_map = {}

    rv = {
        "leafs" : set(),
        "mask"  : {}
    }

    for name, c in inspect.getmembers(m_types, inspect.isclass):
        if not issubclass(c, m_types.Type):  # pragma: no cover
            continue
        nv_map[name] = graph.Vertex_Root(cls_graph, name)
    for name, c in inspect.getmembers(m_types, inspect.isclass):
        for base in c.__bases__:
            if issubclass(base, m_types.Type):
                cls_graph.add_edge(nv_map[base.__name__],
                                   nv_map[name])

    # Get a set of leaf nodes (since these are the only useful results
    # of inference)
    for vrt in cls_graph.vertices:
        if not vrt.out_edges:
            rv["leafs"].add(vrt.name)

    # Get mask for each type. Not ideal, ideally we have a transitive
    # closure algorithm in the graph class, but this works for now.
    def add_mask(base, vrt):
        rv["mask"][base].add(vrt.name)
        for child in vrt.out_edges:
            add_mask(base, child)
    for vrt in cls_graph.vertices:
        rv["mask"][vrt.name] = set()
        add_mask(vrt.name, vrt)

        # Reduce mask by just including the leaves
        rv["mask"][vrt.name] &= rv["leafs"]

    return rv


class Type_Inference:
    MASKS = build_masks()

    def __init__(self):
        self.options = copy(Type_Inference.MASKS["leafs"])

    def is_resolved(self):
        return len(self.options) == 1

    def is_conflicted(self):
        return len(self.options) == 0

    def assert_positive(self, choice):
        assert issubclass(choice, m_types.Type)
        self.options &= Type_Inference.MASKS["mask"][choice.__name__]

    def assert_negative(self, choice):
        assert issubclass(choice, m_types.Type)
        self.options -= Type_Inference.MASKS["mask"][choice.__name__]

    def dump(self):
        print("Type inference")
        print("  resolved: %s" % self.is_resolved())
        print("  conflict: %s" % self.is_conflicted())
        print("  options:  %s" % ", ".join(sorted(self.options)))


def sanity_test():
    inf = Type_Inference()

    inf.dump()

    inf.assert_positive(m_types.Numeric_Type)
    inf.dump()

    inf.assert_negative(m_types.Integer_Type)
    inf.dump()

    inf.assert_positive(m_types.Scalar_Type)
    inf.dump()


if __name__ == "__main__":
    sanity_test()
