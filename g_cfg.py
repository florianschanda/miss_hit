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

from graph import Graph, Vertex_Root
from m_ast import *


class Vertex(Vertex_Root):
    def __init__(self, graph, n_node):
        assert isinstance(n_node, Node)

        super().__init__(graph)

        self.n_node = n_node

    def dot_label(self):
        return "%s" % self.n_node.__class__.__name__


def build_cfg_statement(graph, n_statement):
    assert isinstance(graph, Graph)
    assert isinstance(n_statement, Statement)

    v_entry = Vertex(graph, n_statement)
    v_exits = []
    if isinstance(n_statement, (Compound_Assignment_Statement,
                                Global_Statement,
                                Import_Statement,
                                Naked_Expression_Statement,
                                Persistent_Statement,
                                Simple_Assignment_Statement)):
        # All of these are simple statements
        v_exits.append(v_entry)

    elif isinstance(n_statement, If_Statement):
        current_link = v_entry
        last_action = None
        for n_action in n_statement.l_actions:
            v_action = Vertex(graph, n_action)
            last_action = v_action
            graph.add_edge(current_link, v_action)
            current_link = v_action

            action_entry, action_exits = build_cfg_sos(graph, n_action.n_body)
            graph.add_edge(v_action, action_entry)
            v_exits += action_exits

        if not n_statement.has_else:
            v_exits.append(last_action)

    elif isinstance(n_statement, For_Loop_Statement):
        loop_entry, loop_exits = build_cfg_sos(graph, n_statement.n_body)
        graph.add_edge(v_entry, loop_entry)

        for src in loop_exits:
            graph.add_edge(src, v_entry)

        v_exits = [v_entry]

    else:
        raise ICE("unknown statement kind %s" %
                  n_statement.__class__.__name__)

    return v_entry, v_exits


def build_cfg_sos(graph, n_sos):
    assert isinstance(graph, Graph)
    assert isinstance(n_sos, Sequence_Of_Statements)

    v_entry = None
    current_exits = []
    for n_statement in n_sos.l_statements:
        new_entry, new_exits = build_cfg_statement(graph, n_statement)
        if v_entry is None:
            v_entry = new_entry
        for src in current_exits:
            graph.add_edge(src, new_entry)
        current_exits = new_exits

    return v_entry, current_exits


def build_cfg(n_fdef):
    assert isinstance(n_fdef, (Function_Definition,
                               Script_File))

    graph = Graph()
    v_start = Vertex_Root(graph, "start")
    v_end = Vertex_Root(graph, "end")

    if isinstance(n_fdef, Function_Definition):
        v_entry, v_exits = build_cfg_sos(graph, n_fdef.n_block)
        graph.add_edge(v_start, v_entry)
        for v_exit in v_exits:
            graph.add_edge(v_exit, v_end)
        graph.debug_write_dot(str(n_fdef.n_sig.n_name))

    else:
        v_entry, v_exits = build_cfg_sos(graph, n_fdef.n_statements)
        graph.add_edge(v_start, v_entry)
        for v_exit in v_exits:
            graph.add_edge(v_exit, v_end)
        graph.debug_write_dot(n_fdef.name)
