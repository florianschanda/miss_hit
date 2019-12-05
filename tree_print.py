#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2019, Florian Schanda                         ##
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

# pylint: disable=wildcard-import,unused-wildcard-import
from m_ast import *
# pylint: enable=wildcard-import,unused-wildcard-import


def rec(indent, prefix, node):
    def emit(text):
        print((" " * indent) +
              prefix +
              text)

    if isinstance(node, Simple_Assignment_Statement):
        emit("Assignment on line %u" % node.t_eq.location.line)
        rec(indent + 2, "dst: ", node.n_lhs)
        rec(indent + 2, "src: ", node.n_rhs)

    elif isinstance(node, Compound_Assignment_Statement):
        emit("Assignment on line %u" % node.t_eq.location.line)
        for n, n_lhs in enumerate(node.l_lhs):
            rec(indent + 2, "dst%u: " % n, n_lhs)
        rec(indent + 2, "src: ", node.n_rhs)

    elif isinstance(node, If_Statement):
        emit("If statement on line %u" % node.actions[0][0].location.line)
        for t_kw, n_expr, n_body in node.actions:
            if t_kw.value() in ("if", "elseif"):
                rec(indent + 2,
                    "%s expr: " % t_kw.value(),
                    n_expr)
            rec(indent + 2,
                "%s body: " % t_kw.value(),
                n_body)

    elif isinstance(node, Simple_For_Statement):
        emit("For statement on line %u" % node.t_for.location.line)
        rec(indent + 2, "var: ", node.n_ident)
        rec(indent + 2, "range: ", node.n_range)
        rec(indent + 2, "body: ", node.n_body)

    elif isinstance(node, While_Statement):
        emit("While statement on line %u" % node.t_while.location.line)
        rec(indent + 2, "guard: ", node.n_guard)
        rec(indent + 2, "body: ", node.n_body)

    elif isinstance(node, Return_Statement):
        emit("Return statement on line %u" % node.t_kw.location.line)

    elif isinstance(node, Naked_Expression_Statement):
        rec(indent, prefix + "Naked Expression: ", node.n_expr)

    elif isinstance(node, Sequence_Of_Statements):
        if len(node.statements) == 0:
            emit("")
        elif len(node.statements) == 1:
            rec(indent, prefix, node.statements[0])
        else:
            emit("Sequence_Of_Statements")
            for statement in node.statements:
                rec(indent + 2, "", statement)

    elif isinstance(node, Unary_Operation):
        emit("Unary operation %s" % node.t_op.value())
        rec(indent + 2, "", node.n_expr)

    elif isinstance(node, Binary_Operation):
        emit("Binary operation %s" % node.t_op.value())
        rec(indent + 2, "lhs: ", node.n_lhs)
        rec(indent + 2, "rhs: ", node.n_rhs)

    elif isinstance(node, Range_Expression):
        emit("Range")
        rec(indent + 2, "first: ", node.n_first)
        if node.n_stride:
            rec(indent + 2, "stride: ", node.n_stride)
        rec(indent + 2, "last: ", node.n_last)

    elif isinstance(node, Matrix_Expression):
        emit("Matrix (%ux%u)" % (len(node.items[0]), len(node.items)))
        for row_id, row in enumerate(node.items, 1):
            for item in row:
                rec(indent + 2, "row %u: " % row_id, item)

    elif isinstance(node, Reference):
        if len(node.arglist) == 0:
            rec(indent, prefix, node.n_ident)
        else:
            rec(indent, prefix + "Reference: ", node.n_ident)
            for arg in node.arglist:
                rec(indent + 2, "arg: ", arg)

    elif isinstance(node, String_Literal):
        emit("\"%s\"" % node.t_string.value())

    elif isinstance(node, Number_Literal):
        emit(node.t_value.value())

    elif isinstance(node, Identifier):
        emit(node.t_ident.value())

    elif isinstance(node, Selection):
        emit("Selection of field %s" % node.n_field.t_ident.value())
        rec(indent + 2, "root: ", node.n_root)

    else:
        emit("\033[31;1mTODO\033[0m <" + node.__class__.__name__ + ">")


def treepr(root_node):
    assert isinstance(root_node, Node)
    rec(0, "", root_node)
