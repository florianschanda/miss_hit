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


class CFG_Context:
    def __init__(self, v_entry=None):
        assert v_entry is None or isinstance(v_entry, Vertex_Root)

        self.v_entry = v_entry
        self.l_exits = []
        self.l_loop_breaks = []
        self.l_loop_continues = []

    def merge_loops(self, other):
        assert isinstance(other, CFG_Context)

        self.l_loop_breaks += other.l_loop_breaks
        self.l_loop_continues += other.l_loop_continues

    def merge_exits(self, other):
        assert isinstance(other, CFG_Context)
        self.l_exits += other.l_exits


def build_cfg_statement(graph, n_statement):
    assert isinstance(graph, Graph)
    assert isinstance(n_statement, Statement)

    ctx = CFG_Context(Vertex(graph, n_statement))

    if isinstance(n_statement, (Compound_Assignment_Statement,
                                Global_Statement,
                                Import_Statement,
                                Naked_Expression_Statement,
                                Persistent_Statement,
                                Simple_Assignment_Statement)):
        # All of these are simple statements. One entry, one obvious
        # exit.
        ctx.l_exits.append(ctx.v_entry)

    elif isinstance(n_statement, If_Statement):
        # If statements chain together the actions.
        current_link = ctx.v_entry
        for n_action in n_statement.l_actions:
            v_action = Vertex(graph, n_action)
            graph.add_edge(current_link, v_action)
            current_link = v_action

            action_ctx = build_cfg_sos(graph, n_action.n_body)
            ctx.merge_loops(action_ctx)
            ctx.merge_exits(action_ctx)
            graph.add_edge(v_action, action_ctx.v_entry)

        if not n_statement.has_else:
            # Add an implicit path for else, if not present
            ctx.l_exits.append(current_link)

    elif isinstance(n_statement, For_Loop_Statement):
        # Loops add a loop back to the loop statement. There are two
        # paths out of the loop statement: one into the loop and one
        # to the next statement.
        #
        # Any break statements found in the body are processed here.
        body_ctx = build_cfg_sos(graph, n_statement.n_body)

        graph.add_edge(ctx.v_entry, body_ctx.v_entry)

        for src in body_ctx.l_exits:
            graph.add_edge(src, ctx.v_entry)
        for src in body_ctx.l_loop_continues:
            graph.add_edge(src, ctx.v_entry)

        ctx.l_exits = [ctx.v_entry] + ctx.l_loop_breaks

    elif isinstance(n_statement, Break_Statement):
        ctx.l_loop_breaks.append(ctx.v_entry)

    elif isinstance(n_statement, Continue_Statement):
        ctx.l_loop_continues.append(ctx.v_entry)

    elif isinstance(n_statement, Return_Statement):
        graph.add_edge(ctx.v_entry, graph.get_named_vertex("end"))

    else:
        raise ICE("unknown statement kind %s" %
                  n_statement.__class__.__name__)

    return ctx


def build_cfg_sos(graph, n_sos):
    assert isinstance(graph, Graph)
    assert isinstance(n_sos, Sequence_Of_Statements)

    ctx = CFG_Context()

    for n_statement in n_sos.l_statements:
        statement_ctx = build_cfg_statement(graph, n_statement)

        # Set entry point to the first entry point in the statement
        # list.
        if ctx.v_entry is None:
            ctx.v_entry = statement_ctx.v_entry

        # Link the previous exits to the just processed statement. We
        # then update our exists to the exits of the processed
        # statement.
        for src in ctx.l_exits:
            graph.add_edge(src, statement_ctx.v_entry)
        ctx.l_exits = statement_ctx.l_exits

        # Accumulate loop breaks
        ctx.merge_loops(statement_ctx)

    return ctx


def build_cfg(n_fdef):
    assert isinstance(n_fdef, (Function_Definition,
                               Script_File))

    graph = Graph()
    v_start = Vertex_Root(graph, "start")
    v_end = Vertex_Root(graph, "end")

    if isinstance(n_fdef, Function_Definition):
        ctx = build_cfg_sos(graph, n_fdef.n_block)
    else:
        ctx = build_cfg_sos(graph, n_fdef.n_statements)

    assert len(ctx.l_loop_breaks) == 0

    graph.add_edge(v_start, ctx.v_entry)
    for v_exit in ctx.l_exits:
        graph.add_edge(v_exit, v_end)

    if isinstance(n_fdef, Function_Definition):
        graph.debug_write_dot(str(n_fdef.n_sig.n_name))
    else:
        graph.debug_write_dot(n_fdef.name)
