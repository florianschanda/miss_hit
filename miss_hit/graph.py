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

# A simple graph library that we use to build e.g. the CFG

import os

from miss_hit_core.errors import ICE


class Vertex_Root:
    def __init__(self, graph, name=None):
        assert isinstance(graph, Graph)
        assert name is None or isinstance(name, str)

        self.graph = graph
        self.uid = graph.get_next_uid()
        self.out_edges = set()
        self.in_edges = set()
        self.name = name

        # Register vertex with host graph
        self.graph.vertices.add(self)

        # Register named vertex
        if name:
            if name in graph.names:
                raise ICE("attempted to create named vertex %s that"
                          " already exists" % name)
            self.graph.names[name] = self

    def dot_label(self):
        if self.name:
            return self.name
        else:
            return "vertex %u" % self.uid

    def __lt__(self, other):
        """Comparison for sorting vertices"""
        return self.uid < other.uid


class Graph:
    def __init__(self):
        self.vertices = set()
        self.names = {}
        self.uid_counter = 0

    def get_next_uid(self):
        self.uid_counter += 1
        return self.uid_counter

    def get_named_vertex(self, name):
        assert isinstance(name, str)

        if name not in self.names:
            raise ICE("attempted to get named vertex %s that"
                      " does not exists" % name)

        return self.names[name]

    def add_edge(self, src, dst):
        """ Add src -> dst edge, if it does not exist yet """
        assert isinstance(src, Vertex_Root)
        assert isinstance(dst, Vertex_Root)
        assert src.graph == self
        assert dst.graph == self

        src.out_edges.add(dst)
        dst.in_edges.add(src)

    def remove_edge(self, src, dst):
        """ Removes src -> dst edge, if it exists """
        assert isinstance(src, Vertex_Root)
        assert isinstance(dst, Vertex_Root)
        assert src.graph == self
        assert dst.graph == self

        if dst in src.out_edges:
            src.out_edges.remove(dst)
            dst.in_edges.remove(src)

    def debug_write_dot(self, filename):
        with open(filename + ".dot", "w") as fd:
            fd.write("digraph G {\n")
            for vert in sorted(self.vertices):
                fd.write("  %u [label=\"%s\"];\n" %
                         (vert.uid,
                          vert.dot_label()))
            fd.write("\n")
            for src in sorted(self.vertices):
                for dst in sorted(src.out_edges):
                    fd.write("  %u -> %u;\n" %
                             (src.uid, dst.uid))
            fd.write("}\n")

    def debug_write_pdf(self, filename):  # pragma: no cover
        self.debug_write_dot(filename)
        os.system("dot -Tpdf -o%s.pdf %s.dot" % (filename, filename))

    def count_vertices(self):
        return len(self.vertices)

    def count_edges(self):
        return sum(len(v.out_edges) for v in self.vertices)


def sanity_check():
    class Debug_Vertex(Vertex_Root):
        pass

    graph = Graph()

    v_start = Debug_Vertex(graph, "start")
    v_0 = Debug_Vertex(graph)
    v_end = Debug_Vertex(graph, "end")

    # Sanity check graph names work
    assert v_start == graph.get_named_vertex("start")

    graph.add_edge(v_start, v_0)
    graph.add_edge(v_0, v_end)

    print("vertices: %u" % graph.count_vertices())
    print("edges:    %u" % graph.count_edges())
    graph.debug_write_dot("test1")

    graph.remove_edge(v_start, v_0)

    print("vertices: %u" % graph.count_vertices())
    print("edges:    %u" % graph.count_edges())
    graph.debug_write_dot("test2")


if __name__ == "__main__":
    sanity_check()
