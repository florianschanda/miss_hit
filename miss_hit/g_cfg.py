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

from miss_hit.graph import Graph, Vertex_Root
from miss_hit_core.m_ast import *
from miss_hit_core.errors import Message_Handler, ICE


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
    assert isinstance(n_statement, (Statement,
                                    Metric_Justification_Pragma))

    ctx = CFG_Context(Vertex(graph, n_statement))

    if isinstance(n_statement, (Compound_Assignment_Statement,
                                Global_Statement,
                                Import_Statement,
                                Naked_Expression_Statement,
                                Persistent_Statement,
                                Simple_Assignment_Statement,
                                Metric_Justification_Pragma)):
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
            if action_ctx.v_entry:
                graph.add_edge(v_action, action_ctx.v_entry)

        if not n_statement.has_else:
            # Add an implicit path for else, if not present
            ctx.l_exits.append(current_link)

    elif isinstance(n_statement, Switch_Statement):
        # Case statements in MATLAB are chained, because there is no
        # semantic check that the options do not overlap; hence they
        # must be evaluated in sequence. This is the same as above. In
        # the future, for the MISS_HIT subset, we could make sure
        # there is no overlap.

        current_link = ctx.v_entry
        for n_action in n_statement.l_actions:
            v_action = Vertex(graph, n_action)
            graph.add_edge(current_link, v_action)
            current_link = v_action

            action_ctx = build_cfg_sos(graph, n_action.n_body)
            ctx.merge_loops(action_ctx)
            ctx.merge_exits(action_ctx)
            if action_ctx.v_entry:
                graph.add_edge(v_action, action_ctx.v_entry)

        if not n_statement.has_otherwise:
            # Add an implicit path for otherwise, if not present
            ctx.l_exits.append(current_link)

    elif isinstance(n_statement, (For_Loop_Statement,
                                  While_Statement)):
        # Loops add a loop back to the loop statement. There are two
        # paths out of the loop statement: one into the loop and one
        # to the next statement.
        #
        # Any break statements found in the body are processed here.
        body_ctx = build_cfg_sos(graph, n_statement.n_body)

        if body_ctx.v_entry:
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

    elif isinstance(n_statement, SPMD_Statement):
        spmd_ctx = build_cfg_sos(graph, n_statement.n_body)
        ctx.merge_loops(spmd_ctx)
        ctx.merge_exits(spmd_ctx)

        if spmd_ctx.v_entry:
            graph.add_edge(ctx.v_entry, spmd_ctx.v_entry)

    elif isinstance(n_statement, Try_Statement):
        try_ctx = build_cfg_sos(graph, n_statement.n_body)
        ctx.merge_loops(try_ctx)
        ctx.merge_exits(try_ctx)

        if n_statement.n_handler:
            handler_ctx = build_cfg_sos(graph, n_statement.n_handler)
            ctx.merge_loops(handler_ctx)
            ctx.merge_exits(handler_ctx)
            if handler_ctx.v_entry:
                graph.add_edge(ctx.v_entry, handler_ctx.v_entry)
        else:
            ctx.l_exits.append(ctx.v_entry)

        if try_ctx.v_entry:
            graph.add_edge(ctx.v_entry, try_ctx.v_entry)

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
        ctx = build_cfg_sos(graph, n_fdef.n_body)
    else:
        ctx = build_cfg_sos(graph, n_fdef.n_statements)

    assert len(ctx.l_loop_breaks) == 0

    if ctx.v_entry:
        graph.add_edge(v_start, ctx.v_entry)
        for v_exit in ctx.l_exits:
            graph.add_edge(v_exit, v_end)
    else:
        graph.add_edge(v_start, v_end)

    return graph


def debug_cfg(cunit, mh):
    assert isinstance(cunit, Compilation_Unit)
    assert isinstance(mh, Message_Handler)

    class Function_Visitor(AST_Visitor):
        def visit(self, node, n_parent, relation):
            if isinstance(node, (Function_Definition,
                                 Script_File)):
                # pylint: disable=unused-variable
                cfg = build_cfg(node)
                # if isinstance(n_fdef, Function_Definition):
                #     graph.debug_write_dot(str(n_fdef.n_sig.n_name))
                # else:
                #     graph.debug_write_dot(n_fdef.name)

    cunit.visit(None, Function_Visitor(), "Root")
