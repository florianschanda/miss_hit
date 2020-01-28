#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2019-2020, Florian Schanda                    ##
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

import subprocess

from m_lexer import MATLAB_Token
from errors import ICE


NODE_UID = [0]


class AST_Visitor:
    def visit(self, node, n_parent, relation):
        pass

    def visit_end(self, node, n_parent, relation):
        pass


class Node:
    """ Root class for AST. Everything is a Node. """
    def __init__(self):
        NODE_UID[0] += 1
        self.uid = NODE_UID[0]
        self.n_parent = None

    def set_parent(self, n_parent):
        assert isinstance(n_parent, Node)
        self.n_parent = n_parent

    def debug_parse_tree(self):
        pass

    def _visit(self, parent, function, relation):
        # This function must not be overwritten
        assert parent is None or isinstance(parent, Node)
        assert isinstance(function, AST_Visitor)
        assert isinstance(relation, str)
        function.visit(self, parent, relation)

    def _visit_end(self, parent, function, relation):
        # This function must not be overwritten
        assert parent is None or isinstance(parent, Node)
        assert isinstance(function, AST_Visitor)
        assert isinstance(relation, str)
        function.visit_end(self, parent, relation)

    def _visit_list(self, the_list, function, relation):
        # This function must not be overwritten
        for the_node in the_list:
            the_node.visit(self, function, relation)

    def visit(self, parent, function, relation):
        # This function should be over-written by each node to
        # implement the visitor pattern.
        self._visit(parent, function, relation)
        self._visit_end(parent, function, relation)

    def pp_node(self, fd=None):
        self.visit(None, Text_Visitor(fd), "Root")


##############################################################################
# Some top-level groupings
##############################################################################


class Entity(Node):
    """ Not needed yet - but will become the special nodes we store
        information about symbols.
    """
    pass


class Expression(Node):
    pass


class Name(Expression):
    pass


class Literal(Expression):
    pass


class Definition(Node):
    pass


class Statement(Node):
    def set_parent(self, n_parent):
        assert isinstance(n_parent, Sequence_Of_Statements)
        super().set_parent(n_parent)


class Simple_Statement(Statement):
    pass


class Compound_Statement(Statement):
    pass


class Compilation_Unit(Node):
    def __init__(self, name):
        super().__init__()
        assert isinstance(name, str)

        self.name         = name
        # Not a node since it comes from the filename

    def set_parent(self, n_parent):
        raise ICE("compilation unit cannot have a parent")


##############################################################################
# Compilation units
##############################################################################


class Script_File(Compilation_Unit):
    def __init__(self, name, n_statements, l_functions):
        super().__init__(name)
        assert isinstance(n_statements, Sequence_Of_Statements)
        assert isinstance(l_functions, list)
        for n_function in l_functions:
            assert isinstance(n_function, Function_Definition)

        self.n_statements = n_statements
        self.n_statements.set_parent(self)
        # The main body of the script file

        self.l_functions = l_functions
        for n_function in self.l_functions:
            n_function.set_parent(self)
        # Auxiliary functions the script may define.

    def debug_parse_tree(self):
        dotpr("scr_" + str(self.name) + ".dot", self.n_statements)
        subprocess.run(["dot", "-Tpdf",
                        "scr_" + str(self.name) + ".dot",
                        "-oscr_" + str(self.name) + ".pdf"])

        for n_function in self.l_functions:
            n_function.debug_parse_tree()

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_statements.visit(self, function, "Statements")
        self._visit_list(self.l_functions, function, "Functions")
        self._visit_end(parent, function, relation)


class Function_File(Compilation_Unit):
    def __init__(self, name, l_functions):
        super().__init__(name)
        assert isinstance(l_functions, list)
        assert len(l_functions) >= 1
        for n_function in l_functions:
            assert isinstance(n_function, Function_Definition)

        self.l_functions = l_functions
        for n_function in self.l_functions:
            n_function.set_parent(self)
        # The list of functions we define. The first one is the entry
        # point, the others are auxiliary (but not nested) functions.

    def debug_parse_tree(self):
        for n_function in self.l_functions:
            n_function.debug_parse_tree()

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self._visit_list(self.l_functions, function, "Functions")
        self._visit_end(parent, function, relation)


class Class_File(Compilation_Unit):
    def __init__(self, name, n_classdef, l_functions):
        super().__init__(name)
        assert isinstance(n_classdef, Class_Definition)
        assert isinstance(l_functions, list)
        for n_function in l_functions:
            assert isinstance(n_function, Function_Definition)

        self.n_classdef = n_classdef
        self.n_classdef.set_parent(self)
        # The single class definition for this unit

        self.l_functions = l_functions
        for n_function in self.l_functions:
            n_function.set_parent(self)
        # Auxiliary (but not nested) functions that can appear after
        # the class definition.

    def debug_parse_tree(self):
        dotpr("cls_" + str(self.name) + ".dot", self.n_classdef)
        subprocess.run(["dot", "-Tpdf",
                        "cls_" + str(self.name) + ".dot",
                        "-ocls_" + str(self.name) + ".pdf"])

        for n_function in self.l_functions:
            n_function.debug_parse_tree()

        for n_block in self.n_classdef.l_methods:
            for n_item in n_block.l_items:
                if isinstance(n_item, Function_Definition):
                    n_item.debug_parse_tree()

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_classdef.visit(self, function, "Classdef")
        self._visit_list(self.l_functions, function, "Functions")
        self._visit_end(parent, function, relation)


##############################################################################
# Definitions
##############################################################################


class Class_Definition(Definition):
    def __init__(self, t_classdef, n_name, l_attr, l_super):
        super().__init__()
        assert isinstance(t_classdef, MATLAB_Token)
        assert t_classdef.kind == "KEYWORD" and \
            t_classdef.value == "classdef"
        assert isinstance(n_name, Name)
        assert isinstance(l_attr, list)
        for n_attr in l_attr:
            assert isinstance(n_attr, Name_Value_Pair)
        assert isinstance(l_super, list)
        for n_super in l_super:
            assert isinstance(n_super, Name)

        self.t_classdef = t_classdef
        # Token for the classdef

        self.n_name = n_name
        self.n_name.set_parent(self)
        # (Simple dotted) name of the class

        self.l_super = l_super
        for n_superclass in self.l_super:
            n_superclass.set_parent(self)
        # Optional list of superclasses

        self.l_attr = l_attr
        for n_attr in self.l_attr:
            n_attr.set_parent(self)
        # Optional list of class attributes

        self.l_properties = []
        self.l_events = []
        self.l_enumerations = []
        self.l_methods = []
        # List of special class blocks

    def set_parent(self, n_parent):
        assert isinstance(n_parent, Class_File)
        super().set_parent(n_parent)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_name.visit(self, function, "Name")
        self._visit_list(self.l_super, function, "Superclasses")
        self._visit_list(self.l_attr, function, "Attributes")
        self._visit_list(self.l_properties, function, "Properties")
        self._visit_list(self.l_events, function, "Events")
        self._visit_list(self.l_enumerations, function, "Enumerations")
        self._visit_list(self.l_methods, function, "Methods")
        self._visit_end(parent, function, relation)

    def add_block(self, n_block):
        assert isinstance(n_block, Special_Block)

        if n_block.kind() == "properties":
            self.l_properties.append(n_block)
        elif n_block.kind() == "methods":
            self.l_methods.append(n_block)
        elif n_block.kind() == "events":
            self.l_events.append(n_block)
        elif n_block.kind() == "enumeration":
            self.l_enumerations.append(n_block)
        else:
            raise ICE("unexpected block kind %s" % n_block.kind())

        n_block.set_parent(self)


class Function_Definition(Definition):
    def __init__(self, t_fun, n_sig,
                 l_validation, n_body, l_nested):
        super().__init__()
        assert isinstance(t_fun, MATLAB_Token)
        assert t_fun.kind == "KEYWORD" and t_fun.value == "function"
        assert isinstance(n_sig, Function_Signature)
        assert isinstance(l_validation, list)
        for n in l_validation:
            assert isinstance(n, Special_Block)
        assert isinstance(n_body, Sequence_Of_Statements)
        assert isinstance(l_nested, list)
        for n in l_nested:
            assert isinstance(n, Function_Definition)

        self.t_fun = t_fun
        # The 'function' token

        self.n_sig = n_sig
        self.n_sig.set_parent(self)
        # The function signature i.e. name, inputs, and outputs

        self.l_validation = l_validation
        for n_block in self.l_validation:
            n_block.set_parent(self)
        # Optional list of function argument validation blocks (new in
        # MATLAB 2019b).

        self.n_body = n_body
        self.n_body.set_parent(self)
        # Function body

        self.l_nested = l_nested
        for n_fdef in self.l_nested:
            n_fdef.set_parent(self)
        # Optional list of nested functions

    def set_parent(self, n_parent):
        assert isinstance(n_parent, (Compilation_Unit,
                                     Special_Block,
                                     Function_Definition))
        super().set_parent(n_parent)

    def debug_parse_tree(self):
        dotpr("fun_" + str(self.n_sig.n_name) + ".dot", self)
        subprocess.run(["dot", "-Tpdf",
                        "fun_" + str(self.n_sig.n_name) + ".dot",
                        "-ofun_" + str(self.n_sig.n_name) + ".pdf"])

        for n_function in self.l_nested:
            n_function.debug_parse_tree()

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_sig.visit(self, function, "Signature")
        self._visit_list(self.l_validation, function, "Validation")
        self.n_body.visit(self, function, "Body")
        self._visit_list(self.l_nested, function, "Nested")
        self._visit_end(parent, function, relation)


##############################################################################
# Nodes
##############################################################################


class Function_Signature(Node):
    def __init__(self, n_name, l_inputs, l_outputs):
        super().__init__()
        assert isinstance(n_name, Name)
        assert isinstance(l_inputs, list)
        for n in l_inputs:
            assert isinstance(n, Identifier), \
                str(n) + " is %s and not an Identifier" % n.__class__.__name__
        assert isinstance(l_outputs, list)
        for n in l_outputs:
            assert isinstance(n, Identifier)

        self.n_name = n_name
        self.n_name.set_parent(self)
        # (Simple dotted) name of the function

        self.l_inputs  = l_inputs
        for n_input in self.l_inputs:
            n_input.set_parent(self)
        # List of inputs

        self.l_outputs = l_outputs
        for n_output in self.l_outputs:
            n_output.set_parent(self)
        # List of outputs

    def set_parent(self, n_parent):
        assert isinstance(n_parent, (Function_Definition,
                                     Special_Block))
        # Signatures can also appear naked in class method blocks, in
        # which case they are forward declarations for separately
        # implemented functions.
        super().set_parent(n_parent)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_name.visit(self, function, "Name")
        self._visit_list(self.l_inputs, function, "Inputs")
        self._visit_list(self.l_outputs, function, "Outputs")
        self._visit_end(parent, function, relation)


class Sequence_Of_Statements(Node):
    def __init__(self, l_statements):
        super().__init__()
        assert isinstance(l_statements, list)
        for statement in l_statements:
            assert isinstance(statement, Statement)

        self.l_statements = l_statements
        for n_statement in self.l_statements:
            n_statement.set_parent(self)
        # The list of statements

    def set_parent(self, n_parent):
        assert isinstance(n_parent, (Compound_Statement,
                                     Script_File,
                                     Action,
                                     Function_Definition))
        super().set_parent(n_parent)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self._visit_list(self.l_statements, function, "Statements")
        self._visit_end(parent, function, relation)


class Name_Value_Pair(Node):
    """ AST for items of the various attribute lists inside classdefs

    For example (Access = protected)
    """
    def __init__(self, n_name, n_value=None):
        super().__init__()
        assert isinstance(n_name, Identifier)
        assert n_value is None or isinstance(n_value, Expression)

        self.n_name = n_name
        self.n_name.set_parent(self)
        # The name

        self.n_value = n_value
        if self.n_value:
            self.n_value.set_parent(self)
        # The (optional) value

    def set_parent(self, n_parent):
        assert isinstance(n_parent, (Special_Block,
                                     Class_Definition))
        # Usually appears on the special blocks, but can also appear
        # directly on a classdef.
        super().set_parent(n_parent)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_name.visit(self, function, "Name")
        if self.n_value:
            self.n_value.visit(self, function, "Value")
        self._visit_end(parent, function, relation)


class Special_Block(Node):
    """ AST for properties, methods, events, enumeration and argument
        validation blocks.
    """
    def __init__(self, t_kw, l_attr):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value in ("properties",
                                                         "methods",
                                                         "events",
                                                         "enumeration",
                                                         "arguments")
        assert isinstance(l_attr, list)
        for n_attr in l_attr:
            assert isinstance(n_attr, Name_Value_Pair)

        self.t_kw = t_kw
        # The token (which we also use to distinguish between the 5
        # different kinds of special block).

        self.l_attr = l_attr
        for n_attr in self.l_attr:
            n_attr.set_parent(self)
        # An optional list of attributes that applies to all items in
        # the block.

        self.l_items = []
        # List of items in this block

    def set_parent(self, n_parent):
        assert isinstance(n_parent, (Class_Definition,
                                     Function_Definition))
        super().set_parent(n_parent)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self._visit_list(self.l_attr, function, "Attributes")
        self._visit_list(self.l_items, function, "Items")
        self._visit_end(parent, function, relation)

    def kind(self):
        return self.t_kw.value

    def add_constraint(self, n_cons):
        assert isinstance(n_cons, Entity_Constraints)
        assert self.kind() in ("properties", "arguments")
        self.l_items.append(n_cons)
        n_cons.set_parent(self)

    def add_method(self, n_method):
        assert isinstance(n_method, (Function_Definition, Function_Signature))
        assert self.kind() == "methods"
        self.l_items.append(n_method)
        n_method.set_parent(self)

    def add_enumeration(self, n_enum):
        assert isinstance(n_enum, Class_Enumeration)
        assert self.kind() == "enumeration"
        self.l_items.append(n_enum)
        n_enum.set_parent(self)

    def add_event(self, n_event):
        assert isinstance(n_event, Identifier)
        assert self.kind() == "events"
        self.l_items.append(n_event)
        n_event.set_parent(self)


class Entity_Constraints(Node):
    """ AST for a class property or argument validation found inside
        a properties or arguments block.
    """
    def __init__(self, n_name,
                 l_dim_constraint, n_class_constraint, l_fun_constraint,
                 n_default_value):
        super().__init__()
        assert isinstance(n_name, Name)
        assert isinstance(l_dim_constraint, list)
        assert len(l_dim_constraint) != 1
        for n_dim_constraint in l_dim_constraint:
            assert isinstance(n_dim_constraint, MATLAB_Token)
            assert n_dim_constraint.kind in ("NUMBER", "COLON")
        assert n_class_constraint is None or isinstance(n_class_constraint,
                                                        Name)
        assert isinstance(l_fun_constraint, list)
        for n_fun_constraint in l_fun_constraint:
            assert isinstance(n_fun_constraint, Name)
        assert n_default_value is None or isinstance(n_default_value,
                                                     Expression)

        self.n_name = n_name
        self.n_name.set_parent(self)
        # The entity name we refer to

        self.l_dim_constraint = l_dim_constraint
        # List of optional dimension constraints. Must either be 0 or
        # more than 2. These are number/colon tokens and not
        # expressions.

        self.n_class_constraint = n_class_constraint
        if self.n_class_constraint:
            self.n_class_constraint.set_parent(self)
        # An optional class name our entity must fit

        self.l_fun_constraint = l_fun_constraint
        for n_fun_constraint in self.l_fun_constraint:
            n_fun_constraint.set_parent(self)
        # An optional list of functional constraints our entity must
        # meet.

        self.n_default_value = n_default_value
        if self.n_default_value:
            self.n_default_value.set_parent(self)
        # An optional default value expression

    def set_parent(self, n_parent):
        assert isinstance(n_parent, Special_Block)
        assert n_parent.kind() in ("properties", "arguments")
        super().set_parent(n_parent)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_name.visit(self, function, "Name")
        if self.n_class_constraint:
            self.n_class_constraint.visit(self, function, "Class")
        self._visit_list(self.l_fun_constraint, function, "Functions")
        if self.n_default_value:
            self.n_default_value.visit(self, function, "Default")
        self._visit_end(parent, function, relation)


class Class_Enumeration(Node):
    """ AST for enumeration literal/constructors inside classdefs """
    def __init__(self, n_name, l_args):
        super().__init__()
        assert isinstance(n_name, Identifier)
        assert isinstance(l_args, list)
        for n_arg in l_args:
            assert isinstance(n_arg, Expression)

        self.n_name = n_name
        self.n_name.set_parent(self)
        # Name to introduce enumeration literal

        self.l_args = l_args
        for n_arg in self.l_args:
            n_arg.set_parent(self)
        # Parameters for class constructor to build this literal

    def set_parent(self, n_parent):
        assert isinstance(n_parent, Special_Block)
        assert n_parent.kind() == "enumeration"
        super().set_parent(n_parent)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_name.visit(self, function, "Name")
        self._visit_list(self.l_args, function, "Arguments")
        self._visit_end(parent, function, relation)


class Action(Node):
    """ AST node for actions in if or switch statements. """
    def __init__(self, t_kw, n_expr, n_body):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD"
        assert t_kw.value in ("if", "elseif", "else", "case", "otherwise")
        if t_kw.value in ("else", "otherwise"):
            assert n_expr is None
        else:
            assert isinstance(n_expr, Expression)
        assert isinstance(n_body, Sequence_Of_Statements)

        self.t_kw = t_kw
        # The token to classify this action

        self.n_expr = n_expr
        if self.n_expr:
            self.n_expr.set_parent(self)
        # An optional guard

        self.n_body = n_body
        self.n_body.set_parent(self)

    def kind(self):
        return self.t_kw.value

    def set_parent(self, n_parent):
        if self.kind() in ("if", "elseif", "else"):
            assert isinstance(n_parent, If_Statement)
        else:
            assert isinstance(n_parent, Switch_Statement)
        super().set_parent(n_parent)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        if self.n_expr:
            self.n_expr.visit(parent, function, "Guard")
        self.n_body.visit(parent, function, "Body")
        self._visit_end(parent, function, relation)


class Row(Node):
    """ AST for matrix or cell array rows. """
    def __init__(self, l_items):
        super().__init__()
        assert isinstance(l_items, list)
        # assert len(l_items) >= 1
        # TODO: Investigate if this empty rows should be pruned
        for n_item in l_items:
            assert isinstance(n_item, Expression)

        self.l_items = l_items
        for n_item in self.l_items:
            n_item.set_parent(self)
        # Members of this row

    def set_parent(self, n_parent):
        assert isinstance(n_parent, (Matrix_Expression,
                                     Cell_Expression))
        super().set_parent(n_parent)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self._visit_list(self.l_items, function, "Items")
        self._visit_end(parent, function, relation)


##############################################################################
# Names
##############################################################################


class Reference(Name):
    """ Proto AST for identifier + brackets. Could be an array reference
        or a function call. Will be re-written later to Array_Index (TODO)
        or Function_Call by semantic analysis.
    """
    def __init__(self, n_ident, arglist):
        super().__init__()
        assert isinstance(n_ident, Name)
        assert isinstance(arglist, list)
        for arg in arglist:
            assert isinstance(arg, Expression)

        self.n_ident = n_ident
        self.n_ident.set_parent(self)
        # An identifier

        self.l_args = arglist
        for n_arg in self.l_args:
            n_arg.set_parent(self)
        # A list of parameters or indices

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_ident.visit(self, function, "Name")
        self._visit_list(self.l_args, function, "Arguments")
        self._visit_end(parent, function, relation)

    def __str__(self):
        if self.l_args:
            return "%s(%s)" % (self.n_ident, ", ".join(map(str, self.l_args)))
        else:
            return str(self.n_ident)


class Cell_Reference(Name):
    def __init__(self, n_ident, arglist):
        super().__init__()
        assert isinstance(n_ident, Name)
        assert isinstance(arglist, list)
        for arg in arglist:
            assert isinstance(arg, Expression)

        self.n_ident = n_ident
        self.n_ident.set_parent(self)
        # An identifier

        self.l_args = arglist
        for n_arg in self.l_args:
            n_arg.set_parent(self)
        # A list of indices

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_ident.visit(self, function, "Name")
        self._visit_list(self.l_args, function, "Arguments")
        self._visit_end(parent, function, relation)

    def __str__(self):
        if self.l_args:
            return "%s{%s}" % (self.n_ident, ", ".join(map(str, self.l_args)))
        else:
            return str(self.n_ident)


class Identifier(Name):
    def __init__(self, t_ident):
        super().__init__()
        assert isinstance(t_ident, MATLAB_Token)
        assert t_ident.kind == "IDENTIFIER" or \
            (t_ident.kind == "OPERATOR" and t_ident.value == "~") or \
            (t_ident.kind == "KEYWORD" and t_ident.value == "end") or \
            t_ident.kind == "BANG"

        self.t_ident = t_ident
        # The token

    def __str__(self):
        if self.t_ident.kind == "BANG":
            return "system"
        else:
            return self.t_ident.value


class Selection(Name):
    def __init__(self, t_selection, n_prefix, n_field):
        super().__init__()
        assert isinstance(t_selection, MATLAB_Token)
        assert t_selection.kind == "SELECTION"
        assert isinstance(n_prefix, Name)
        assert isinstance(n_field, Identifier)

        self.t_selection = t_selection
        # The . token

        self.n_prefix = n_prefix
        self.n_prefix.set_parent(self)
        # The stuff befor the .

        self.n_field = n_field
        self.n_field.set_parent(self)
        # The stuff after the .

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_prefix.visit(self, function, "Prefix")
        self.n_field.visit(self, function, "Field")
        self._visit_end(parent, function, relation)

    def __str__(self):
        return "%s.%s" % (self.n_prefix, self.n_field)


class Dynamic_Selection(Name):
    def __init__(self, t_selection, n_prefix, n_field):
        super().__init__()
        assert isinstance(t_selection, MATLAB_Token)
        assert t_selection.kind == "SELECTION"
        assert isinstance(n_prefix, Name)
        assert isinstance(n_field, Expression)

        self.t_selection = t_selection
        # The token for .

        self.n_prefix = n_prefix
        self.n_prefix.set_parent(self)
        # The stuff befor the .

        self.n_field = n_field
        self.n_field.set_parent(self)
        # The stuff in the brackets after the .

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_prefix.visit(self, function, "Prefix")
        self.n_field.visit(self, function, "Field")
        self._visit_end(parent, function, relation)

    def __str__(self):
        return "%s.(%s)" % (self.n_prefix, self.n_field)


class Superclass_Reference(Name):
    def __init__(self, t_at, n_prefix, n_reference):
        super().__init__()
        assert isinstance(t_at, MATLAB_Token)
        assert t_at.kind == "AT"
        assert isinstance(n_prefix, Name)
        assert isinstance(n_reference, Name)

        self.t_at = t_at
        # The token for @

        self.n_prefix = n_prefix
        self.n_prefix.set_parent(self)
        # Stuff before the @

        self.n_reference = n_reference
        self.n_reference.set_parent(self)
        # Stuff after the @

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_prefix.visit(self, function, "Prefix")
        self.n_reference.visit(self, function, "Reference")
        self._visit_end(parent, function, relation)

    def __str__(self):
        return "%s@%s" % (self.n_prefix, self.n_reference)


##############################################################################
# Compound Statements
##############################################################################


class For_Loop_Statement(Compound_Statement):
    def __init__(self, t_for, n_ident, n_body):
        super().__init__()
        assert isinstance(t_for, MATLAB_Token)
        assert t_for.kind == "KEYWORD" and t_for.value in ("for",
                                                           "parfor")
        assert isinstance(n_ident, Identifier)
        assert isinstance(n_body, Sequence_Of_Statements)

        self.t_for = t_for
        # The token for the for or parfor

        self.n_ident = n_ident
        self.n_ident.set_parent(self)
        # The name of the iterator

        self.n_body = n_body
        self.n_body.set_parent(self)
        # The body for the loop

    def visit(self, parent, function, relation):
        raise ICE("reached visit procedure for abstract base class for"
                  " for-loops")


class Simple_For_Statement(For_Loop_Statement):
    def __init__(self, t_for, n_ident, n_range, n_body):
        super().__init__(t_for, n_ident, n_body)
        assert t_for.kind == "KEYWORD" and t_for.value == "for"
        assert isinstance(n_range, Range_Expression)

        self.n_range = n_range
        self.n_range.set_parent(self)
        # The range expression for the loop bounds

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_ident.visit(parent, function, "Identifier")
        self.n_range.visit(parent, function, "Range")
        self.n_body.visit(parent, function, "Body")
        self._visit_end(parent, function, relation)


class General_For_Statement(For_Loop_Statement):
    def __init__(self, t_for, n_ident, n_expr, n_body):
        super().__init__(t_for, n_ident, n_body)
        assert t_for.kind == "KEYWORD" and t_for.value == "for"
        assert isinstance(n_expr, Expression)

        self.n_expr = n_expr
        self.n_expr.set_parent(self)
        # An expression returning some kind of matrix which defines
        # our loop bounds

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_ident.visit(parent, function, "Identifier")
        self.n_expr.visit(parent, function, "Expression")
        self.n_body.visit(parent, function, "Body")
        self._visit_end(parent, function, relation)


class Parallel_For_Statement(For_Loop_Statement):
    def __init__(self, t_for, n_ident, n_range, n_body, n_workers):
        super().__init__(t_for, n_ident, n_body)
        assert t_for.kind == "KEYWORD" and t_for.value == "parfor"
        assert isinstance(n_range, Range_Expression)
        assert n_workers is None or isinstance(n_workers, Expression)

        self.n_range = n_range
        self.n_range.set_parent(self)
        # The range expression for the loop bounds

        self.n_workers = n_workers
        if self.n_workers:
            self.n_workers.set_parent(self)
        # An optional indication of how work is distributed.

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_ident.visit(parent, function, "Identifier")
        self.n_range.visit(parent, function, "Range")
        if self.n_workers:
            self.n_workers.visit(parent, function, "Workers")
        self.n_body.visit(parent, function, "Body")
        self._visit_end(parent, function, relation)


class While_Statement(Compound_Statement):
    def __init__(self, t_while, n_guard, n_body):
        super().__init__()
        assert isinstance(t_while, MATLAB_Token)
        assert t_while.kind == "KEYWORD" and t_while.value == "while"
        assert isinstance(n_guard, Expression)
        assert isinstance(n_body, Sequence_Of_Statements)

        self.t_while = t_while
        # The token for while

        self.n_guard = n_guard
        self.n_guard.set_parent(self)
        # The guard expression

        self.n_body = n_body
        self.n_body.set_parent(self)
        # The loop body

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_guard.visit(parent, function, "Guard")
        self.n_body.visit(parent, function, "Body")
        self._visit_end(parent, function, relation)


class If_Statement(Compound_Statement):
    def __init__(self, l_actions):
        super().__init__()
        assert isinstance(l_actions, list)
        assert len(l_actions) >= 1
        for action_id, n_action in enumerate(l_actions, 1):
            assert isinstance(n_action, Action)
            if action_id == 1:
                assert n_action.kind() == "if"
            elif action_id == len(l_actions):
                assert n_action.kind() in ("elseif", "else")
            else:
                assert n_action.kind() == "elseif"

        self.l_actions = l_actions
        for n_actions in self.l_actions:
            n_actions.set_parent(self)
        # List of actions. Starts with an if actions, is followed by
        # zero or more elseif actions, and is terminated by up to one
        # else action.

        self.has_else = self.l_actions[-1].kind() == "else"
        # Cache if we have an else part or not.

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self._visit_list(self.l_actions, function, "Action")
        self._visit_end(parent, function, relation)


class Switch_Statement(Compound_Statement):
    def __init__(self, t_kw, n_switch_expr, l_actions):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value == "switch"
        assert isinstance(n_switch_expr, Expression)
        assert isinstance(l_actions, list)
        assert len(l_actions) >= 1
        for action_id, n_action in enumerate(l_actions, 1):
            assert isinstance(n_action, Action)
            if action_id == len(l_actions):
                assert n_action.kind() in ("case", "otherwise")
            else:
                assert n_action.kind() == "case"

        self.t_kw = t_kw
        # The token for 'switch'

        self.n_expr = n_switch_expr
        self.n_expr.set_parent(self)
        # The expression in the switch statement itself

        self.l_actions = l_actions
        for n_action in self.l_actions:
            n_action.set_parent(self)
        # List of actions. Must be at least one. Case actions followed
        # by up to one otherwise action.

        self.has_otherwise = self.l_actions[-1].kind() == "otherwise"
        # Cache if we have an otherwise or not.

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_expr.visit(parent, function, "Guard")
        self._visit_list(self.l_actions, function, "Action")
        self._visit_end(parent, function, relation)


class Try_Statement(Compound_Statement):
    def __init__(self, t_try, n_body, t_catch, n_ident, n_handler):
        super().__init__()
        assert isinstance(t_try, MATLAB_Token)
        assert t_try.kind == "KEYWORD" and t_try.value == "try"
        if t_catch is not None:
            isinstance(t_catch, MATLAB_Token)
            assert t_catch.kind == "KEYWORD" and t_catch.value == "catch"
        assert isinstance(n_body, Sequence_Of_Statements)
        assert n_handler is None or isinstance(n_handler,
                                               Sequence_Of_Statements)
        assert n_ident is None or isinstance(n_ident,
                                             Identifier)
        assert n_handler is not None or n_ident is None

        self.t_try   = t_try
        self.t_catch = t_catch
        # Tokens for the try and catch part

        self.n_ident = n_ident
        if self.n_ident:
            self.n_ident.set_parent(self)
        # An optional identifier that names the caught exception.

        self.n_body = n_body
        self.n_body.set_parent(self)
        # The body of the try block

        self.n_handler = n_handler
        if self.n_handler:
            self.n_handler.set_parent(self)
        # An optional body for the catch block. If absent then the
        # semantics are to catch and ignore any exceptions, and resume
        # execution with the statement following this block.

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_body.visit(parent, function, "Body")
        if self.n_ident:
            self.n_ident.visit(parent, function, "Identifier")
        if self.n_handler:
            self.n_handler.visit(parent, function, "Handler")
        self._visit_end(parent, function, relation)


class SPMD_Statement(Compound_Statement):
    def __init__(self, t_spmd, n_body):
        super().__init__()
        assert isinstance(t_spmd, MATLAB_Token)
        assert t_spmd.kind == "KEYWORD" and t_spmd.value == "spmd"
        assert isinstance(n_body, Sequence_Of_Statements)

        self.t_spmd = t_spmd
        # The token for the spmd keyword

        self.n_body = n_body
        self.n_body.set_parent(self)
        # The body

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_body.visit(parent, function, "Body")
        self._visit_end(parent, function, relation)


##############################################################################
# Simple Statements
##############################################################################


class Simple_Assignment_Statement(Simple_Statement):
    def __init__(self, t_eq, n_lhs, n_rhs):
        super().__init__()
        assert isinstance(t_eq, MATLAB_Token)
        assert t_eq.kind == "ASSIGNMENT"
        assert isinstance(n_lhs, Name)
        assert isinstance(n_rhs, Expression)

        self.t_eq = t_eq
        # The token for the =

        self.n_lhs = n_lhs
        self.n_lhs.set_parent(self)
        # The target name of the assignment

        self.n_rhs = n_rhs
        self.n_rhs.set_parent(self)
        # The expression to assign

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_lhs.visit(parent, function, "LHS")
        self.n_rhs.visit(parent, function, "RHS")
        self._visit_end(parent, function, relation)


class Compound_Assignment_Statement(Simple_Statement):
    def __init__(self, t_eq, l_lhs, n_rhs):
        super().__init__()
        assert isinstance(t_eq, MATLAB_Token)
        assert t_eq.kind == "ASSIGNMENT"
        assert isinstance(l_lhs, list)
        assert len(l_lhs) >= 2
        for n_lhs in l_lhs:
            assert isinstance(n_lhs, Name)
        assert isinstance(n_rhs, Expression)

        self.t_eq = t_eq
        # The token for the =

        self.l_lhs = l_lhs
        for n_target in self.l_lhs:
            n_target.set_parent(self)
        # The list of assignment targets. At least 2 (other forms are
        # re-written on the fly to Simple_Assignment_Statement.

        self.n_rhs = n_rhs
        self.n_rhs.set_parent(self)
        # The expression to assign. Must be a function call that
        # returns multiple outputs. We can't check it now (during
        # parsing), it will be checked during semantic analysis.

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self._visit_list(self.l_lhs, function, "LHS")
        self.n_rhs.visit(parent, function, "RHS")
        self._visit_end(parent, function, relation)


class Naked_Expression_Statement(Simple_Statement):
    def __init__(self, n_expr):
        super().__init__()
        assert isinstance(n_expr, Expression)

        self.n_expr = n_expr
        self.n_expr.set_parent(self)
        # The expression

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_expr.visit(parent, function, "Expression")
        self._visit_end(parent, function, relation)


class Return_Statement(Simple_Statement):
    def __init__(self, t_kw):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value == "return"

        self.t_kw = t_kw
        # The token for return


class Break_Statement(Simple_Statement):
    def __init__(self, t_kw):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value == "break"

        self.t_kw = t_kw
        # The token for break


class Continue_Statement(Simple_Statement):
    def __init__(self, t_kw):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value == "continue"

        self.t_kw = t_kw
        # The token for continue


class Global_Statement(Simple_Statement):
    def __init__(self, t_kw, l_names):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value == "global"
        assert isinstance(l_names, list)
        for n_name in l_names:
            assert isinstance(n_name, Identifier)

        self.t_kw = t_kw
        # The token for global

        self.l_names = l_names
        for n_name in self.l_names:
            n_name.set_parent(self)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self._visit_list(self.l_names, function, "Names")
        self._visit_end(parent, function, relation)


class Persistent_Statement(Simple_Statement):
    def __init__(self, t_kw, l_names):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value == "persistent"
        assert isinstance(l_names, list)
        for n_name in l_names:
            assert isinstance(n_name, Identifier)

        self.t_kw = t_kw
        # The token for persistent

        self.l_names = l_names
        for n_name in self.l_names:
            n_name.set_parent(self)
        # List of identifiers to make persistent

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self._visit_list(self.l_names, function, "Names")
        self._visit_end(parent, function, relation)


class Import_Statement(Simple_Statement):
    def __init__(self, t_kw, l_chain):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value == "import"
        assert isinstance(l_chain, list)
        for t_item in l_chain:
            assert isinstance(t_item, MATLAB_Token)
            assert t_item.kind == "IDENTIFIER" or \
                (t_item.kind == "OPERATOR" and t_item.value == ".*")

        self.t_kw = t_kw
        # The token for import

        self.l_chain = l_chain
        # The tokens for the namespace to import. Will be identifiers,
        # followed by an optional operator (.*).

    def get_chain_strings(self):
        return [t.value if t.kind == "IDENTIFIER" else "*"
                for t in self.l_chain]


##############################################################################
# Literals
##############################################################################


class Number_Literal(Literal):
    def __init__(self, t_value):
        super().__init__()
        assert isinstance(t_value, MATLAB_Token)
        assert t_value.kind == "NUMBER"

        self.t_value = t_value
        # The token for the number literal

    def __str__(self):
        return self.t_value.value


class Char_Array_Literal(Literal):
    def __init__(self, t_string):
        super().__init__()
        assert isinstance(t_string, MATLAB_Token)
        assert t_string.kind in ("CARRAY", "BANG")

        self.t_string = t_string
        # The token for the char array literal. It can also be a bang
        # token so we can use it as a char array argument to system()
        # when re-writing ! directives to a function call to system.

    def __str__(self):
        return "'" + self.t_string.value + "'"


class String_Literal(Literal):
    def __init__(self, t_string):
        super().__init__()
        assert isinstance(t_string, MATLAB_Token)
        assert t_string.kind == "STRING"

        self.t_string = t_string
        # The token for the string literal.

    def __str__(self):
        return '"' + self.t_string.value + '"'


##############################################################################
# Expressions
##############################################################################


class Reshape(Expression):
    def __init__(self, t_colon):
        super().__init__()
        assert isinstance(t_colon, MATLAB_Token)
        assert t_colon.kind == "COLON"

        self.t_colon = t_colon
        # The token for :

    def set_parent(self, n_parent):
        assert isinstance(n_parent, (Reference,
                                     Cell_Reference))
        # This can only appear in very specific situations. it is not
        # to be confused by a Range_Expression.
        super().set_parent(n_parent)

    def __str__(self):
        return ":"


class Range_Expression(Expression):
    def __init__(self, n_first, n_last, n_stride=None):
        super().__init__()
        assert isinstance(n_first, Expression)
        assert isinstance(n_last, Expression)
        assert n_stride is None or isinstance(n_stride, Expression)

        self.n_first = n_first
        self.n_first.set_parent(self)
        # The inclusive lower bound

        self.n_last = n_last
        self.n_last.set_parent(self)
        # The inclusive upper bound

        self.n_stride = n_stride
        if self.n_stride:
            self.n_stride.set_parent(self)
        # The (optional) stride. It doesn't have to neatly divide the
        # range.

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_first.visit(self, function, "First")
        if self.n_stride:
            self.n_stride.visit(self, function, "Stride")
        self.n_last.visit(self, function, "Last")
        self._visit_end(parent, function, relation)

    def __str__(self):
        if self.n_stride:
            return "%s:%s:%s" % (self.n_first, self.n_stride, self.n_last)
        else:
            return "%s:%s" % (self.n_first, self.n_last)


class Matrix_Expression(Expression):
    def __init__(self, t_open, t_close, l_rows):
        super().__init__()
        assert isinstance(t_open, MATLAB_Token)
        assert t_open.kind == "M_BRA"
        assert isinstance(t_close, MATLAB_Token)
        assert t_close.kind == "M_KET"
        assert isinstance(l_rows, list)
        for n_row in l_rows:
            assert isinstance(n_row, Row)

        self.t_open  = t_open
        self.t_close = t_close
        # The tokens for [ and ]

        self.l_rows = l_rows
        for n_row in self.l_rows:
            n_row.set_parent(self)
        # Matrix rows

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self._visit_list(self.l_rows, function, "Rows")
        self._visit_end(parent, function, relation)


class Cell_Expression(Expression):
    def __init__(self, t_open, t_close, l_rows):
        super().__init__()
        assert isinstance(t_open, MATLAB_Token)
        assert t_open.kind == "C_BRA"
        assert isinstance(t_close, MATLAB_Token)
        assert t_close.kind == "C_KET"
        assert isinstance(l_rows, list)
        for n_row in l_rows:
            assert isinstance(n_row, Row)

        self.t_open  = t_open
        self.t_close = t_close
        # The tokens for { and }

        self.l_rows = l_rows
        for n_row in self.l_rows:
            n_row.set_parent(self)
        # Cell rows

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self._visit_list(self.l_rows, function, "Rows")
        self._visit_end(parent, function, relation)


class Function_Call(Expression):
    def __init__(self, n_name, l_args, variant="normal"):
        super().__init__()
        assert isinstance(n_name, Name)
        assert isinstance(l_args, list)
        for n_arg in l_args:
            assert isinstance(n_arg, Expression)
            if variant in ("command", "escape"):
                assert isinstance(n_arg, Char_Array_Literal)
        assert variant in ("normal", "command", "escape")
        if variant == "escape":
            assert str(n_name) == "system"
            assert len(l_args) == 1

        self.variant = variant
        # The kind of function call we have. Can be normal, command
        # form, or a shell escape.

        self.n_name = n_name
        self.n_name.set_parent(self)
        # Name of the called function. For escapes this is the whole
        # bang identifier. Semantic analysis will assign the correct
        # entity however.

        self.l_args = l_args
        for n_arg in self.l_args:
            n_arg.set_parent(self)
        # List of parameters. Char literals for command form or shell
        # escapes, expressions otherwise.

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        if self.variant != "escape":
            self.n_name.visit(parent, function, "Name")
        self._visit_list(self.l_args, function, "Arguments")
        self._visit_end(parent, function, relation)

    def __str__(self):
        if self.variant == "normal":
            return "%s(%s)" % (self.n_name,
                               ", ".join(map(str, self.l_args)))
        elif self.variant == "command":
            return "%s %s" % (self.n_name,
                              " ".join(map(str, self.l_args)))
        else:
            return "!%s" % str(self.l_args[0])


class Unary_Operation(Expression):
    """ AST for unary operations. While most of them are prefix,
        in MATLAB we have some postfix operators.
    """
    def __init__(self, precedence, t_op, n_expr):
        super().__init__()
        assert 1 <= precedence <= 12
        assert isinstance(t_op, MATLAB_Token)
        assert t_op.kind == "OPERATOR"
        assert t_op.value in ("+", "-", "~", ".'", "'")
        assert isinstance(n_expr, Expression)

        self.precedence = precedence
        # Numeric precedence to determine if brackets are necessary or
        # not.

        self.t_op = t_op
        # The token for the operator symbol

        self.n_expr = n_expr
        self.n_expr.set_parent(self)
        # The expression

        # To support the style checker we flag that this operator is
        # unary.
        self.t_op.fix["unary_operator"] = True

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_expr.visit(parent, function, "Expression")
        self._visit_end(parent, function, relation)

    def __str__(self):
        if self.t_op.value in (".'", "'"):
            # Postfix
            return "%s%s" % (self.n_expr, self.t_op.value)
        else:
            # Prefix
            return "%s%s" % (self.t_op.value, self.n_expr)


class Binary_Operation(Expression):
    def __init__(self, precedence, t_op, n_lhs, n_rhs):
        super().__init__()
        assert 1 <= precedence <= 12
        assert isinstance(t_op, MATLAB_Token)
        assert t_op.kind == "OPERATOR"
        assert isinstance(n_lhs, Expression)
        assert isinstance(n_rhs, Expression)

        self.precedence = precedence
        # Numeric precedence to determine if brackets are necessary or
        # not.

        self.t_op = t_op
        # The token for the operator symbol

        self.n_lhs = n_lhs
        self.n_lhs.set_parent(self)
        # The left-hand expression

        self.n_rhs = n_rhs
        self.n_rhs.set_parent(self)
        # The right-hand expression

        # To support the style checker we flag that this operator is
        # unary.
        self.t_op.fix["binary_operator"] = True

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_lhs.visit(parent, function, "LHS")
        self.n_rhs.visit(parent, function, "RHS")
        self._visit_end(parent, function, relation)

    def __str__(self):
        return "(%s %s %s)" % (self.n_lhs, self.t_op.value, self.n_rhs)


class Lambda_Function(Expression):
    def __init__(self, t_at, l_parameters, n_body):
        super().__init__()
        assert isinstance(t_at, MATLAB_Token)
        assert t_at.kind == "AT"
        assert isinstance(l_parameters, list)
        for param in l_parameters:
            assert isinstance(param, Identifier)
        assert isinstance(n_body, Expression)

        self.t_at = t_at
        # The token for @

        self.l_parameters = l_parameters
        for n_param in self.l_parameters:
            n_param.set_parent(self)
        # Names for the parameters for our lambda function

        self.n_body = n_body
        self.n_body.set_parent(self)
        # The expression

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self._visit_list(self.l_parameters, function, "Parameters")
        self.n_body.visit(parent, function, "Body")
        self._visit_end(parent, function, relation)

    def __str__(self):
        return "@(%s) %s" % (",".join(map(str, self.l_parameters)),
                             str(self.n_body))


class Function_Pointer(Expression):
    def __init__(self, t_at, n_name):
        super().__init__()
        assert isinstance(t_at, MATLAB_Token)
        assert t_at.kind == "AT"
        assert isinstance(n_name, Name)

        self.t_at = t_at
        # The token for @

        self.n_name = n_name
        self.n_name.set_parent(self)
        # The (simple dotted) name of the function we point to

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_name.visit(parent, function, "Name")
        self._visit_end(parent, function, relation)

    def __str__(self):
        return "@" + str(self.n_name)


class Metaclass(Expression):
    def __init__(self, t_mc, n_name):
        super().__init__()
        assert isinstance(t_mc, MATLAB_Token)
        assert t_mc.kind == "METACLASS"
        assert isinstance(n_name, Name)

        self.t_mc = t_mc
        # The token for ?

        self.n_name = n_name
        self.n_name.set_parent(self)
        # The (simple dotted) name of a class

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_name.visit(parent, function, "Name")
        self._visit_end(parent, function, relation)

    def __str__(self):
        return "?" + str(self.n_name)


###################################################################
# Debug output: Text
###################################################################

class Text_Visitor(AST_Visitor):
    def __init__(self, fd):
        super().__init__()
        self.indent = 0
        self.fd = fd

    def write(self, string):
        assert isinstance(string, str)
        txt = " " * (self.indent * 2) + string
        if self.fd:
            self.fd.write(txt + "\n")
        else:
            print(txt)

    def write_head(self, string, relation):
        if relation:
            self.write(relation + ": " + string)
        else:
            self.write(string)
        self.indent += 1

    def visit(self, node, n_parent, relation):
        if isinstance(node, Special_Block):
            self.write_head(node.t_kw.value.capitalize() + " " +
                            node.__class__.__name__,
                            relation)
        elif isinstance(node, Entity_Constraints):
            self.write_head(node.__class__.__name__,
                            relation)
            for dim, t_cons in enumerate(node.l_dim_constraint, 1):
                if t_cons.kind == "COLON":
                    self.write("Dimension %u constraint: %s" %
                               (dim, t_cons.kind))
                else:
                    self.write("Dimension %u constraint: %s" %
                               (dim, t_cons.value))
        elif isinstance(node, Function_Call):
            self.write_head(node.variant.capitalize() + " form " +
                            node.__class__.__name__,
                            relation)
        elif isinstance(node, Action):
            self.write_head(node.kind().capitalize() + " " +
                            node.__class__.__name__,
                            relation)
        elif isinstance(node, Identifier):
            self.write_head(node.__class__.__name__ +
                            " <" + node.t_ident.value + ">",
                            relation)
        elif isinstance(node, Number_Literal):
            self.write_head(node.__class__.__name__ +
                            " <" + node.t_value.value + ">",
                            relation)
        elif isinstance(node, Char_Array_Literal):
            self.write_head(node.__class__.__name__ +
                            " '" + node.t_string.value + "'",
                            relation)
        elif isinstance(node, String_Literal):
            self.write_head(node.__class__.__name__ +
                            " \"" + node.t_string.value + "\"",
                            relation)
        elif isinstance(node, Unary_Operation):
            self.write_head(node.__class__.__name__ + " " + node.t_op.value,
                            relation)
        elif isinstance(node, Binary_Operation):
            self.write_head(node.__class__.__name__ + " " + node.t_op.value,
                            relation)
        elif isinstance(node, Import_Statement):
            self.write_head(node.__class__.__name__ +
                            " for " +
                            ".".join(node.get_chain_strings()),
                            relation)
        else:
            self.write_head(node.__class__.__name__,
                            relation)

    def visit_end(self, node, n_parent, relation):
        self.indent -= 1


###################################################################
# Debug output: Graphviz
###################################################################

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
            if t_kw.value in ("if", "elseif"):
                dot(fd, node, t_kw.value + " guard", n_expr)
            dot(fd, node, t_kw.value + " body", n_body)

    elif isinstance(node, Switch_Statement):
        attr.append("shape=diamond")
        dot(fd, node, "switch expr", node.n_expr)
        for t_kw, n_expr, n_body in node.l_options:
            if t_kw.value == "case":
                dot(fd, node, "case expr", n_expr)
            dot(fd, node, t_kw.value + " body", n_body)

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
        lbl += ".".join(t.value if t.kind == "IDENTIFIER" else "*"
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
        lbl += " %s" % node.t_op.value
        dot(fd, node, "", node.n_expr)

    elif isinstance(node, Binary_Operation):
        lbl += " %s" % node.t_op.value.replace("\\", "\\\\")
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
        if node.l_args:
            for arg in node.l_args:
                dot(fd, node, "arg", arg)
        else:
            attr.append("shape=none")

    elif isinstance(node, Cell_Reference):
        lbl += " to %s" % str(node.n_ident)
        if node.l_args:
            for arg in node.l_args:
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
        attr.append("shape=none")
        dot(fd, node, "prefix", node.n_prefix)
        dot(fd, node, "reference", node.n_reference)

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
        lbl = node.t_kw.value
        for n_attr in node.l_attr:
            dot(fd, node, "attr", n_attr)
        for item in node.l_items:
            dot(fd, node, "", item)

    elif isinstance(node, Name_Value_Pair):
        lbl += " " + str(node.n_name)
        if node.n_value:
            dot(fd, node, "value", node.n_value)

    elif isinstance(node, Entity_Constraints):
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
