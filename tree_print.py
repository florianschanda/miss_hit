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
        emit("Simple for statement on line %u" % node.t_for.location.line)
        rec(indent + 2, "var: ", node.n_ident)
        rec(indent + 2, "range: ", node.n_range)
        rec(indent + 2, "body: ", node.n_body)

    elif isinstance(node, General_For_Statement):
        emit("General for statement on line %u" % node.t_for.location.line)
        rec(indent + 2, "var: ", node.n_ident)
        rec(indent + 2, "expr: ", node.n_expr)
        rec(indent + 2, "body: ", node.n_body)

    elif isinstance(node, While_Statement):
        emit("While statement on line %u" % node.t_while.location.line)
        rec(indent + 2, "guard: ", node.n_guard)
        rec(indent + 2, "body: ", node.n_body)

    elif isinstance(node, Return_Statement):
        emit("Return statement on line %u" % node.t_kw.location.line)

    elif isinstance(node, Break_Statement):
        emit("Break statement on line %u" % node.t_kw.location.line)

    elif isinstance(node, Continue_Statement):
        emit("Continue statement on line %u" % node.t_kw.location.line)

    elif isinstance(node, Naked_Expression_Statement):
        rec(indent, prefix + "Naked Expression: ", node.n_expr)

    elif isinstance(node, Sequence_Of_Statements):
        if len(node.l_statements) == 0:
            emit("")
        elif len(node.l_statements) == 1:
            rec(indent, prefix, node.l_statements[0])
        else:
            emit("Sequence_Of_Statements")
            for statement in node.l_statements:
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

    elif isinstance(node, Cell_Expression):
        emit("Cell (%ux%u)" % (len(node.items[0]), len(node.items)))
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

    elif isinstance(node, Function_Signature):
        emit("Signature for %s" % node.n_name)
        for item in node.l_inputs:
            rec(indent + 2, "input: ", item)
        for item in node.l_outputs:
            rec(indent + 2, "output: ", item)

    elif isinstance(node, Function_Definition):
        emit("Function definition for %s" % node.n_sig.n_name)
        rec(indent + 2, "signature: ", node.n_sig)
        for item in node.l_validation:
            rec(indent + 2, "validation: ", item)
        rec(indent + 2, "body: ", node.n_body)
        for item in node.l_nested:
            rec(indent + 2, "nested: ", item)

    else:
        emit("\033[31;1mTODO\033[0m <" + node.__class__.__name__ + ">")


def treepr(root_node):
    assert isinstance(root_node, Node)
    rec(0, "", root_node)


def dot(fd, parent, annotation, node):
    lbl = node.__class__.__name__
    attr = []

    if isinstance(node, Script_File):
        lbl += " " + node.name
        dot(fd, node, "statements", node.n_statements)
        for n_function in node.l_functions:
            dot(fd, node, "function", n_function)

    elif isinstance(node, Function_Signature):
        dot(fd, node, "name", node.n_name)
        for item in node.l_inputs:
            dot(fd, node, "input", item)
        for item in node.l_outputs:
            dot(fd, node, "output ", item)

    elif isinstance(node, Function_Definition):
        lbl += " for %s" % str(node.n_sig.n_name)

        # Only show the body if this is the root
        if parent is None:
            dot(fd, node, "signature", node.n_sig)
            for item in node.l_validation:
                dot(fd, node, "validation", item)
            dot(fd, node, "body", node.n_body)
            for item in node.l_nested:
                dot(fd, node, "nested", item)

    elif isinstance(node, Simple_Assignment_Statement):
        dot(fd, node, "target", node.n_lhs)
        dot(fd, node, "expression", node.n_rhs)

    elif isinstance(node, Compound_Assignment_Statement):
        for n, n_lhs in enumerate(node.l_lhs, 1):
            dot(fd, node, "target %u" % n, n_lhs)
        dot(fd, node, "expression", node.n_rhs)

    elif isinstance(node, If_Statement):
        attr.append("shape=diamond")
        for t_kw, n_expr, n_body in node.actions:
            if t_kw.value() in ("if", "elseif"):
                dot(fd, node, t_kw.value() + " guard", n_expr)
            dot(fd, node, t_kw.value() + " body", n_body)

    elif isinstance(node, Switch_Statement):
        attr.append("shape=diamond")
        dot(fd, node, "switch expr", node.n_expr)
        for t_kw, n_expr, n_body in node.l_options:
            if t_kw.value() == "case":
                dot(fd, node, "case expr", n_expr)
            dot(fd, node, t_kw.value() + " body", n_body)

    elif isinstance(node, Simple_For_Statement):
        attr.append("shape=diamond")
        dot(fd, node, "var", node.n_ident)
        dot(fd, node, "range", node.n_range)
        dot(fd, node, "body", node.n_body)

    elif isinstance(node, General_For_Statement):
        attr.append("shape=diamond")
        dot(fd, node, "var", node.n_ident)
        dot(fd, node, "range", node.n_expr)
        dot(fd, node, "body", node.n_body)

    elif isinstance(node, Parallel_For_Statement):
        attr.append("shape=diamond")
        dot(fd, node, "var", node.n_ident)
        dot(fd, node, "range", node.n_range)
        if node.n_workers:
            dot(fd, node, "workers", node.n_workers)
        dot(fd, node, "body", node.n_body)

    elif isinstance(node, While_Statement):
        attr.append("shape=diamond")
        dot(fd, node, "guard", node.n_guard)
        dot(fd, node, "body", node.n_body)

    elif isinstance(node, Return_Statement):
        attr.append("shape=diamond")

    elif isinstance(node, Break_Statement):
        attr.append("shape=diamond")

    elif isinstance(node, Continue_Statement):
        attr.append("shape=diamond")

    elif isinstance(node, Naked_Expression_Statement):
        dot(fd, node, "", node.n_expr)

    elif isinstance(node, Global_Statement):
        for n_name in node.l_names:
            dot(fd, node, "", n_name)

    elif isinstance(node, Persistent_Statement):
        for n_name in node.l_names:
            dot(fd, node, "", n_name)

    elif isinstance(node, Import_Statement):
        lbl += "\n"
        lbl += ".".join(t.value() if t.kind == "IDENTIFIER" else "*"
                        for t in node.l_chain)

    elif isinstance(node, Sequence_Of_Statements):
        for statement in node.l_statements:
            dot(fd, node, "", statement)

    elif isinstance(node, Try_Statement):
        attr.append("shape=diamond")
        dot(fd, node, "try", node.n_body)
        if node.n_ident:
            dot(fd, node, "ident", node.n_ident)
        if node.n_handler:
            dot(fd, node, "catch", node.n_handler)

    elif isinstance(node, SPMD_Statement):
        dot(fd, node, "body", node.n_body)

    elif isinstance(node, Unary_Operation):
        lbl += " %s" % node.t_op.value()
        dot(fd, node, "", node.n_expr)

    elif isinstance(node, Binary_Operation):
        lbl += " %s" % node.t_op.value().replace("\\", "\\\\")
        dot(fd, node, "", node.n_lhs)
        dot(fd, node, "", node.n_rhs)

    elif isinstance(node, Range_Expression):
        dot(fd, node, "first", node.n_first)
        if node.n_stride:
            dot(fd, node, "stride", node.n_stride)
        dot(fd, node, "last", node.n_last)

    elif isinstance(node, Matrix_Expression):
        lbl = "%ux%u %s\\n%s" % (len(node.items[0]),
                                 len(node.items),
                                 lbl,
                                 str(node).replace("; ", "\\n"))
        attr.append("shape=none")

    elif isinstance(node, Cell_Expression):
        lbl = "%ux%u %s\\n%s" % (len(node.items[0]),
                                 len(node.items),
                                 lbl,
                                 str(node).replace("; ", "\\n"))
        attr.append("shape=none")

    elif isinstance(node, Reference):
        lbl += " to %s" % str(node.n_ident)
        if node.arglist:
            for arg in node.arglist:
                dot(fd, node, "arg", arg)
        else:
            attr.append("shape=none")

    elif isinstance(node, Cell_Reference):
        lbl += " to %s" % str(node.n_ident)
        if node.arglist:
            for arg in node.arglist:
                dot(fd, node, "arg", arg)
        else:
            attr.append("shape=none")

    elif isinstance(node, String_Literal):
        lbl += "\\n" + str(node)
        attr.append("shape=none")

    elif isinstance(node, Char_Array_Literal):
        lbl += "\\n" + str(node)
        attr.append("shape=none")

    elif isinstance(node, Number_Literal):
        lbl += "\\n" + str(node)
        attr.append("shape=none")

    elif isinstance(node, Identifier):
        lbl += "\\n" + str(node)
        attr.append("shape=none")

    elif isinstance(node, Selection):
        dot(fd, node, "prefix", node.n_prefix)
        dot(fd, node, "field", node.n_field)

    elif isinstance(node, Dynamic_Selection):
        dot(fd, node, "prefix", node.n_prefix)
        dot(fd, node, "field", node.n_field)

    elif isinstance(node, Superclass_Reference):
        lbl += "\\n" + str(node)
        attr.append("shape=none")

    elif isinstance(node, Lambda_Function):
        attr.append("shape=box")
        for param in node.l_parameters:
            dot(fd, node, "param", param)
        dot(fd, node, "body", node.n_body)

    elif isinstance(node, Function_Pointer):
        attr.append("shape=box")
        lbl += "\\nto " + str(node.n_name)

    elif isinstance(node, Metaclass):
        attr.append("shape=none")
        lbl += " of " + str(node.n_name)

    elif isinstance(node, Function_Call):
        lbl = "Call to %s" % str(node.n_name)
        if node.variant != "normal":
            lbl += " in %s form" % node.variant
        for n, n_arg in enumerate(node.l_args, 1):
            dot(fd, node, "arg %u" % n, n_arg)

    elif isinstance(node, Class_Definition):
        lbl += " of %s" % str(node.n_name)
        for n_super in node.l_super:
            dot(fd, node, "super", n_super)
        for n_attr in node.l_attr:
            dot(fd, node, "attr", n_attr)
        for n in (node.l_properties +
                  node.l_events +
                  node.l_enumerations +
                  node.l_methods):
            dot(fd, node, "block", n)

    elif isinstance(node, Special_Block):
        lbl = node.t_kw.value()
        for n_attr in node.l_attr:
            dot(fd, node, "attr", n_attr)
        for item in node.l_items:
            dot(fd, node, "", item)

    elif isinstance(node, Class_Attribute):
        lbl += " " + str(node.n_name)
        if node.n_value:
            dot(fd, node, "value", node.n_value)

    elif isinstance(node, Class_Property):
        lbl = str(node.n_name)
        attr.append("shape=none")

        if node.n_default_value:
            dot(fd, node, "default", node.n_default_value)
        for n, n_dim in enumerate(node.l_dim_constraint, 1):
            dot(fd, node, "dim %u" % n, n_dim)
        if node.n_class_constraint:
            dot(fd, node, "class", node.n_class_constraint)
        for n_fun in node.l_fun_constraint:
            dot(fd, node, "constraint", n_fun)

    elif isinstance(node, Class_Enumeration):
        lbl = str(node.n_name)
        attr.append("shape=none")

        for n, n_arg in enumerate(node.l_args, 1):
            dot(fd, node, "arg %u" % n, n_arg)

    elif isinstance(node, MATLAB_Token):
        attr.append("shape=box")
        attr.append("style=filled")
        attr.append("fillcolor=gray")
        lbl = node.kind + "\\n" + node.raw_text

    else:
        lbl = "TODO: " + lbl
        attr.append("fillcolor=yellow")
        attr.append("style=filled")

    attr.append("label=\"%s\"" % lbl.replace("\"", "\\\""))
    fd.write("  %u [%s];\n" % (hash(node), ",".join(attr)))

    if parent:
        fd.write("  %u -> %s [label=\"%s\"];" % (hash(parent),
                                                 hash(node),
                                                 annotation))


def dotpr(filename, root_node):
    assert isinstance(filename, str)
    assert isinstance(root_node, Node)
    with open(filename, "w") as fd:
        fd.write("digraph G {\n")
        dot(fd, None, "", root_node)
        fd.write("}\n")
