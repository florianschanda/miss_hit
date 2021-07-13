#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2019-2021, Florian Schanda                    ##
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
import re
import os

from copy import copy

from miss_hit_core.config import Config
from miss_hit_core.m_language import TOKEN_KINDS
from miss_hit_core.m_language_builtins import HIGH_IMPACT_BUILTIN_FUNCTIONS
from miss_hit_core.errors import Message_Handler, ICE, Location


##############################################################################
# Lexical tokens
##############################################################################

TOKENS_WITH_IMPLICIT_VALUE = frozenset([
    "COMMA",
    "SEMICOLON",
    "COLON",
    "BRA", "KET",      # ( )
    "C_BRA", "C_KET",  # { }
    "M_BRA", "M_KET",  # [ ] for matrices
    "A_BRA", "A_KET",  # [ ] for assignment targets
    "ASSIGNMENT",
    "SELECTION",
    "AT",
    "METACLASS"
])
assert TOKENS_WITH_IMPLICIT_VALUE <= TOKEN_KINDS


class Autofix_Instruction:
    def __init__(self):
        self.ensure_trim_before = False
        self.ensure_trim_after  = False
        self.ensure_ws_before   = False
        self.ensure_ws_after    = False
        # Control whitespace before/after token

        self.ensure_maxgap_before = False
        self.ensure_maxgap_after  = False
        # Make sure there is at most 1 whitespace around this token

        self.delete = False
        # Remove this token

        self.correct_indent = None
        # The correct level of indentation

        self.replace_with_newline = False
        # For CONTINUATION tokens. Means this continuation should be
        # just a newline (or comment) instead.

        self.change_to_semicolon = False
        # Replace this (comma) token with a semicolon

        self.add_semicolon_after = False
        # Insert a new semicolon after this token

        self.add_newline = False
        # Insert a newline after this token.

        # The following are not fixes as such, but extra annotation to
        # produce fixes.

        self.binary_operator = False
        self.unary_operator  = False
        # Classification if this token is a unary or binary
        # operator. Only set for OPERATOR tokens.

        self.spurious = False
        # Classification for spurious tokens. Specifically this can be
        # set on commas so that mh_style can remove them.

        self.statement_terminator = False
        # Classification if this comma/semicolon token actually ends a
        # statement. I.e. not true for the punctuation inside matrices
        # or cells.

        self.flag_continuations = False
        # Set in cases where continuations following this token would
        # be highly problematic

        self.make_shortcircuit_explicit = False
        # Set for & and | inside if/while guards to change them into
        # the explicit short-circuit form && or ||


class MATLAB_Token:
    def __init__(self,
                 kind,
                 raw_text,
                 location,
                 first_in_line,
                 first_in_statement,
                 value = None,
                 anonymous = False,
                 contains_quotes = False,
                 block_comment = False,
                 annotation = False):
        assert kind in TOKEN_KINDS
        assert isinstance(raw_text, str)
        assert isinstance(location, Location)
        assert isinstance(first_in_line, bool)
        assert isinstance(first_in_statement, bool)
        assert isinstance(anonymous, bool)
        assert isinstance(contains_quotes, bool)
        assert isinstance(block_comment, bool)
        assert isinstance(annotation, bool)
        assert not contains_quotes or kind in ("STRING", "CARRAY")

        self.kind               = kind
        self.raw_text           = raw_text
        self.location           = location
        self.first_in_line      = first_in_line
        self.first_in_statement = first_in_statement
        self.anonymous          = anonymous
        self.contains_quotes    = contains_quotes
        self.block_comment      = block_comment
        self.annotation         = annotation

        if value is None:
            if self.kind in TOKENS_WITH_IMPLICIT_VALUE:
                self.value = None
            elif self.kind == "CONTINUATION":
                self.value = self.raw_text[3:].strip()
            elif self.kind == "COMMENT":
                if self.block_comment:
                    self.value = self.raw_text.strip()
                else:
                    self.value = self.raw_text[1:].strip()
            elif self.kind in ("CARRAY", "STRING"):
                if self.contains_quotes:
                    self.value = self.raw_text[1:-1]
                else:
                    self.value = self.raw_text
            elif self.kind == "BANG":
                self.value = self.raw_text[1:]
            else:
                self.value = self.raw_text
        else:
            self.value = value

        # A free-form dictionary where we can record autofix
        # requirements.
        self.fix = Autofix_Instruction()

        # A link back to the AST so that we can identify to which node
        # tokens nominally belong.
        self.ast_link = None

    def get_unstripped_comment(self):
        assert self.kind == "COMMENT"
        if self.block_comment:
            return self.raw_text
        else:
            return self.raw_text[1:]

    def set_ast(self, node):
        assert isinstance(node, Node)
        self.ast_link = node

    def __repr__(self):
        star = "*" if self.anonymous else ""

        if self.value is None or self.kind == "NEWLINE":
            return "Token%s(%s)" % (star, self.kind)
        elif self.kind == "COMMENT" and self.block_comment:
            return "Token%s(BLOCK%s, <<%s>>)" % (star, self.kind, self.value)
        else:
            return "Token%s(%s, <<%s>>)" % (star, self.kind, self.value)


##############################################################################
# AST
##############################################################################


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

    def loc(self):
        raise ICE("cannot produce error location")

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

    def causes_indentation(self):
        if isinstance(self, If_Statement):
            # We do not indent for this, since the if actions
            # indent instead.
            return False

        elif isinstance(self, (Action,
                               Special_Block,
                               Class_Definition,
                               Function_Definition,
                               Compound_Statement)):
            return True

        else:
            return False

    def get_indentation(self):
        # Indentation is the same level as the parent. + 1 if the
        # parent itself causes children to be indented.

        if self.n_parent:
            indent = self.n_parent.get_indentation()
            if self.n_parent.causes_indentation():
                indent += 1
        else:
            indent = 0

        return indent


##############################################################################
# Some top-level groupings
##############################################################################


class Expression(Node):
    def __init__(self):
        super().__init__()

        self.t_bracket_open = None
        self.t_bracket_close = None
        # Tokens for the () around this expression

    def set_enclosing_brackets(self, t_open, t_close):
        assert isinstance(t_open, MATLAB_Token)
        assert isinstance(t_close, MATLAB_Token)
        assert t_open.kind == "BRA"
        assert t_close.kind == "KET"

        self.t_bracket_open = t_open
        self.t_bracket_open.set_ast(self)

        self.t_bracket_close = t_close
        self.t_bracket_close.set_ast(self)

    def evaluate_static_string_expression(self):
        raise ICE("not a static string expression")


class Name(Expression):
    def is_simple_dotted_name(self):
        return False

    def sty_check_builtin_shadow(self, mh, cfg):
        assert isinstance(mh, Message_Handler)
        assert isinstance(cfg, Config)


class Literal(Expression):
    pass


class Definition(Node):
    def __init__(self):
        super().__init__()

        self.n_docstring = None
        # Optional docstring (the first set of unbroken
        # comments). Note that this is not produced by the parser, but
        # can be set by other (comment aware) tools such as MH Style.

    def set_docstring(self, n_docstring):
        assert isinstance(n_docstring, Docstring)
        self.n_docstring = n_docstring
        self.n_docstring.set_parent(self)

    def get_local_name(self):
        raise ICE("get_local_name not implemented")


class Pragma(Node):
    def __init__(self, t_pragma, t_kind):
        super().__init__()
        assert isinstance(t_pragma, MATLAB_Token)
        assert t_pragma.kind == "KEYWORD" and t_pragma.value == "pragma"
        assert isinstance(t_kind, MATLAB_Token)
        assert t_kind.kind == "IDENTIFIER"

        self.t_pragma = t_pragma
        self.t_pragma.set_ast(self)
        # The pragma token

        self.t_kind = t_kind
        self.t_kind.set_ast(self)
        # The pragma kind

    def loc(self):
        return self.t_pragma.location

    def set_parent(self, n_parent):
        assert isinstance(n_parent, (Sequence_Of_Statements,
                                     Compilation_Unit))
        super().set_parent(n_parent)


class Statement(Node):
    def set_parent(self, n_parent):
        assert isinstance(n_parent, Sequence_Of_Statements)
        super().set_parent(n_parent)


class Simple_Statement(Statement):
    pass


class Compound_Statement(Statement):
    pass


class Compilation_Unit(Node):
    # pylint: disable=unused-argument
    def __init__(self, name, dirname, loc, file_length):
        super().__init__()
        assert isinstance(name, str)
        assert isinstance(dirname, str)
        assert isinstance(loc, Location)
        assert isinstance(file_length, int) and file_length >= 0

        self.name = name
        # Not a node since it comes from the filename

        self.dirname = dirname
        # Name of the directory; relevant later to sort out which
        # package we're part of

        self.error_location = loc
        # In case we need to attach a message to the compilation unit
        # itself

        self.file_length = file_length
        # The number of lines in this file

        self.scope = None
        # Set by m_sem, will contain the symbol table for this unit

        self.n_docstring = None
        # Optional docstring (the first set of unbroken
        # comments). Note that this is not produced by the parser, but
        # can be set by other (comment aware) tools such as MH Style.

    def loc(self):
        return self.error_location

    def set_parent(self, n_parent):
        raise ICE("compilation unit cannot have a parent")

    def sty_check_naming(self, mh, cfg):
        assert isinstance(mh, Message_Handler)
        assert isinstance(cfg, Config)
        raise ICE("compilation unit root implements no checks")

    def set_docstring(self, n_docstring):
        assert isinstance(n_docstring, Docstring)
        self.n_docstring = n_docstring
        self.n_docstring.set_parent(self)

    def get_name_prefix(self):
        rv = ""
        cdir = os.path.normpath(self.dirname)
        while True:
            dname = os.path.basename(cdir)
            cdir = os.path.dirname(cdir)
            if dname.startswith("+"):
                rv = dname[1:] + "." + rv
            elif dname.startswith("@"):
                rv = dname[1:] + "::" + rv
            else:
                break
        return rv


##############################################################################
# Compilation units
##############################################################################


class Script_File(Compilation_Unit):
    def __init__(self,
                 name, dirname, loc, file_length,
                 n_statements, l_functions, l_pragmas):
        super().__init__(name, dirname, loc, file_length)
        assert isinstance(n_statements, Sequence_Of_Statements)
        assert isinstance(l_functions, list)
        for n_function in l_functions:
            assert isinstance(n_function, Function_Definition)
        assert isinstance(l_pragmas, list)
        for n_pragma in l_pragmas:
            assert isinstance(n_pragma, Pragma)

        self.n_statements = n_statements
        self.n_statements.set_parent(self)
        # The main body of the script file

        self.n_statements.prepend_pragmas(l_pragmas)
        # The list of pragmas we found so far actually belongs to the
        # statement list in this file.

        self.l_functions = l_functions
        for n_function in self.l_functions:
            n_function.set_parent(self)
        # Auxiliary functions the script may define.

    def debug_parse_tree(self):
        dotpr("scr_" + str(self.name) + ".dot", self.n_statements)
        subprocess.run(["dot", "-Tpdf",
                        "scr_" + str(self.name) + ".dot",
                        "-oscr_" + str(self.name) + ".pdf"],
                       check=False)

        for n_function in self.l_functions:
            n_function.debug_parse_tree()

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_statements.visit(self, function, "Statements")
        self._visit_list(self.l_functions, function, "Functions")
        self._visit_end(parent, function, relation)

    def sty_check_naming(self, mh, cfg):
        assert isinstance(mh, Message_Handler)
        assert isinstance(cfg, Config)
        for n_function in self.l_functions:
            n_function.sty_check_naming(mh, cfg)

        if cfg.active("naming_scripts"):
            regex = cfg.style_config["regex_script_name"]
            file_root = self.name.rsplit(".", 1)[0]
            if not re.match("^(" + regex + ")$", file_root):
                mh.style_issue(self.loc(),
                               "violates naming scheme for scripts")

    def get_local_name(self):
        return self.name.rsplit(".", 1)[0]


class Function_File(Compilation_Unit):
    def __init__(self,
                 name, dirname, loc, file_length,
                 l_functions, is_separate, l_pragmas):
        super().__init__(name, dirname, loc, file_length)
        assert isinstance(l_functions, list)
        assert len(l_functions) >= 1
        for n_function in l_functions:
            assert isinstance(n_function, Function_Definition)
        assert isinstance(is_separate, bool)
        assert isinstance(l_pragmas, list)
        for n_pragma in l_pragmas:
            assert isinstance(n_pragma, Pragma)

        self.l_functions = l_functions
        for n_function in self.l_functions:
            n_function.set_parent(self)
        # The list of functions we define. The first one is the entry
        # point, the others are auxiliary (but not nested) functions.

        self.is_separate = is_separate
        # If true, then this compilation unit resides in a @ directory
        # for classes.

        self.l_pragmas = l_pragmas
        for n_pragma in l_pragmas:
            n_pragma.set_parent(self)
        # A list of pragmas that applies to this compilation unit

    def debug_parse_tree(self):
        for n_function in self.l_functions:
            n_function.debug_parse_tree()

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self._visit_list(self.l_pragmas, function, "Pragmas")
        self._visit_list(self.l_functions, function, "Functions")
        self._visit_end(parent, function, relation)

    def sty_check_naming(self, mh, cfg):
        assert isinstance(mh, Message_Handler)
        assert isinstance(cfg, Config)
        for n_function in self.l_functions:
            n_function.sty_check_naming(mh, cfg)


class Class_File(Compilation_Unit):
    def __init__(self,
                 name, dirname, loc, file_length,
                 n_classdef, l_functions, l_pragmas):
        super().__init__(name, dirname, loc, file_length)
        assert isinstance(n_classdef, Class_Definition)
        assert isinstance(l_functions, list)
        for n_function in l_functions:
            assert isinstance(n_function, Function_Definition)
        assert isinstance(l_pragmas, list)
        for n_pragma in l_pragmas:
            assert isinstance(n_pragma, Pragma)

        self.n_classdef = n_classdef
        self.n_classdef.set_parent(self)
        # The single class definition for this unit

        self.l_functions = l_functions
        for n_function in self.l_functions:
            n_function.set_parent(self)
        # Auxiliary (but not nested) functions that can appear after
        # the class definition.

        self.l_pragmas = l_pragmas
        for n_pragma in l_pragmas:
            n_pragma.set_parent(self)
        # A list of pragmas that applies to this compilation unit

    def debug_parse_tree(self):
        dotpr("cls_" + str(self.name) + ".dot", self.n_classdef)
        subprocess.run(["dot", "-Tpdf",
                        "cls_" + str(self.name) + ".dot",
                        "-ocls_" + str(self.name) + ".pdf"],
                       check=False)

        for n_function in self.l_functions:
            n_function.debug_parse_tree()

        for n_block in self.n_classdef.l_methods:
            for n_item in n_block.l_items:
                if isinstance(n_item, Function_Definition):
                    n_item.debug_parse_tree()

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self._visit_list(self.l_pragmas, function, "Pragmas")
        self.n_classdef.visit(self, function, "Classdef")
        self._visit_list(self.l_functions, function, "Functions")
        self._visit_end(parent, function, relation)

    def sty_check_naming(self, mh, cfg):
        assert isinstance(mh, Message_Handler)
        assert isinstance(cfg, Config)
        self.n_classdef.sty_check_naming(mh, cfg)
        for n_function in self.l_functions:
            n_function.sty_check_naming(mh, cfg)

##############################################################################
# Definitions
##############################################################################


class Class_Definition(Definition):
    def __init__(self, t_classdef):
        super().__init__()
        assert isinstance(t_classdef, MATLAB_Token)
        assert t_classdef.kind == "KEYWORD" and \
            t_classdef.value == "classdef"

        self.entity = None
        # Pointer to the class entity

        self.t_classdef = t_classdef
        self.t_classdef.set_ast(self)
        # Token for the classdef

        self.n_name = None
        # Name of the class. Always a simple identifier, not even dots
        # are allowed here.

        self.n_constructor     = None
        self.n_constructor_sig = None
        # Short-cut to constructor function (if it exists)

        self.l_attr = []
        # Optional list of class attributes

        self.l_super = []
        # Optional list of superclasses

        self.l_properties = []
        self.l_events = []
        self.l_enumerations = []
        self.l_methods = []
        # List of special class blocks

    def loc(self):
        if self.n_name:
            return self.n_name.loc()
        else:
            return self.t_classdef.location

    def set_name(self, n_name):
        assert isinstance(n_name, Identifier)

        self.n_name = n_name
        self.n_name.set_parent(self)

    def set_attributes(self, l_attr):
        assert isinstance(l_attr, list)
        for n_attr in l_attr:
            assert isinstance(n_attr, Name_Value_Pair)

        self.l_attr = l_attr
        for n_attr in self.l_attr:
            n_attr.set_parent(self)

    def get_attribute(self, name):
        assert isinstance(name, str)

        for n_nv_pair in self.l_attr:
            if str(n_nv_pair.n_name) == name:
                return n_nv_pair
        return None

    def set_super_classes(self, l_super):
        assert isinstance(l_super, list)
        for n_super in l_super:
            assert isinstance(n_super, Name)

        self.l_super = l_super
        for n_superclass in self.l_super:
            n_superclass.set_parent(self)

    def set_parent(self, n_parent):
        assert isinstance(n_parent, Class_File)
        super().set_parent(n_parent)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_name.visit(self, function, "Name")
        if self.n_constructor:
            self.n_constructor.visit(self, function, "Constructor")
        elif self.n_constructor_sig:
            self.n_constructor_sig.visit(self,
                                         function,
                                         "Constructor Signature")
        self._visit_list(self.l_super, function, "Superclasses")
        self._visit_list(self.l_attr, function, "Attributes")
        self._visit_list(self.l_properties, function, "Properties")
        self._visit_list(self.l_events, function, "Events")
        self._visit_list(self.l_enumerations, function, "Enumerations")
        self._visit_list(self.l_methods, function, "Methods")
        self._visit_end(parent, function, relation)

    def add_block(self, mh, n_block):
        assert isinstance(mh, Message_Handler)
        assert isinstance(n_block, Special_Block)

        if n_block.kind() == "properties":
            self.l_properties.append(n_block)
        elif n_block.kind() == "methods":
            self.l_methods.append(n_block)
            for n_item in n_block.l_items:
                if isinstance(n_item, Function_Definition):
                    n_con = n_item
                    n_sig = n_item.n_sig
                elif isinstance(n_item, Function_Signature):
                    n_con = None
                    n_sig = n_item
                else:
                    raise ICE("%s item in method block is not function"
                              " signature or function definition" %
                              n_item.__class__.__name__)

                if str(n_sig.n_name) == str(self.n_name):
                    if self.n_constructor_sig is None:
                        self.n_constructor     = n_con
                        self.n_constructor_sig = n_sig
                        n_sig.is_constructor = True
                    else:
                        mh.error(n_item.loc(),
                                 "class can only have one constructor,"
                                 " previous declaration in line %u" %
                                 self.n_constructor_sig.loc().line,
                                 fatal=False)

        elif n_block.kind() == "events":
            self.l_events.append(n_block)
        elif n_block.kind() == "enumeration":
            self.l_enumerations.append(n_block)
        else:
            raise ICE("unexpected block kind %s" % n_block.kind())

        n_block.set_parent(self)

    def sty_check_naming(self, mh, cfg):
        assert isinstance(mh, Message_Handler)
        assert isinstance(cfg, Config)
        if cfg.active("naming_classes"):
            self.n_name.sty_check_naming(mh, cfg, "class")
        for n_block in self.l_methods:
            for n_function in n_block.l_items:
                n_function.sty_check_naming(mh, cfg)
        for n_block in self.l_enumerations:
            for n_enum in n_block.l_items:
                n_enum.sty_check_naming(mh, cfg)

    def get_local_name(self):
        if isinstance(self.n_parent, Class_File):
            return str(self.n_name)
        else:
            raise ICE("logic error: parent of class is %s" %
                      self.n_parent.__class__.__name__)


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
        self.t_fun.set_ast(self)
        # The 'function' token

        self.t_end = None
        # The (optional) end token

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

    def loc(self):
        if self.n_sig.n_name:
            return self.n_sig.loc()
        else:
            return self.t_fun.location

    def set_parent(self, n_parent):
        assert isinstance(n_parent, (Compilation_Unit,
                                     Special_Block,
                                     Function_Definition))
        super().set_parent(n_parent)

    def set_end(self, t_end):
        assert isinstance(t_end, MATLAB_Token)
        assert t_end.kind == "KEYWORD" and t_end.value == "end"

        self.t_end = t_end
        self.t_end.set_ast(self)

    def debug_parse_tree(self):
        dotpr("fun_" + str(self.n_sig.n_name) + ".dot", self)
        subprocess.run(["dot", "-Tpdf",
                        "fun_" + str(self.n_sig.n_name) + ".dot",
                        "-ofun_" + str(self.n_sig.n_name) + ".pdf"],
                       check=False)

        for n_function in self.l_nested:
            n_function.debug_parse_tree()

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_sig.visit(self, function, "Signature")
        self._visit_list(self.l_validation, function, "Validation")
        self.n_body.visit(self, function, "Body")
        self._visit_list(self.l_nested, function, "Nested")
        self._visit_end(parent, function, relation)

    def sty_check_naming(self, mh, cfg):
        assert isinstance(mh, Message_Handler)
        assert isinstance(cfg, Config)
        self.n_sig.sty_check_naming(mh, cfg)
        for n_function in self.l_nested:
            n_function.sty_check_naming(mh, cfg)

    def is_class_method(self):
        # We're a class method in two scenarios:
        #
        # 1. We're directly in a class
        #
        # 2. We're the first function in a function file that is in a
        #    @ directory
        return isinstance(self.n_parent, Special_Block) or \
            (isinstance(self.n_parent, Function_File) and
             self.n_parent.is_separate and
             self.n_parent.l_functions[0] == self)

    def get_local_name(self):
        if isinstance(self.n_parent, Function_File):
            return str(self.n_sig.n_name)
        elif isinstance(self.n_parent, Compilation_Unit):
            return "%s::%s" % (self.n_parent.name,
                               str(self.n_sig.n_name))
        elif isinstance(self.n_parent, Special_Block):
            return "%s::%s" % (self.n_parent.n_parent.get_local_name(),
                               str(self.n_sig.n_name))
        elif isinstance(self.n_parent, Function_Definition):
            return "%s::%s" % (self.n_parent.get_local_name(),
                               str(self.n_sig.n_name))
        else:
            raise ICE("logic error: parent of fn is %s" %
                      self.n_parent.__class__.__name__)


##############################################################################
# Nodes
##############################################################################

class Copyright_Info(Node):
    def __init__(self, n_parent, t_comment, re_match):
        super().__init__()
        assert isinstance(t_comment, MATLAB_Token)
        assert t_comment.kind == "COMMENT"
        # assert isinstance(re_match, re.Match)
        # In 3.6 this is a _sre.SRE_Match object; so we can't easily
        # check for this...

        self.t_comment = t_comment
        self.match = re_match

        self.set_parent(n_parent)

    def is_block_comment(self):
        return self.t_comment.block_comment

    def get_copy_notice(self):
        return self.match.group("copy")

    def get_org(self):
        return self.match.group("org")

    def get_ystart(self):
        return int(self.match.group("ystart"))

    def get_yend(self):
        return int(self.match.group("yend"))

    def get_range(self):
        if self.match.group("ystart"):
            return (self.get_ystart(), self.get_yend())
        else:
            return (self.get_yend(), self.get_yend())

    def get_comment_text_loc(self):
        # Get a location for the actual text of the comment. We need
        # to carefully shift to account for the stripped value
        rv = copy(self.t_comment.location)
        rv.col_start += (len(self.t_comment.raw_text.rstrip()) -
                         len(self.t_comment.value))
        return rv

    def loc_org(self):
        rv = self.get_comment_text_loc()
        rv.col_end = rv.col_start + (self.match.span("org")[1] - 1)
        rv.col_start += self.match.span("org")[0]
        return rv

    def loc_yend(self):
        rv = self.get_comment_text_loc()
        rv.col_end = rv.col_start + (self.match.span("yend")[1] - 1)
        rv.col_start += self.match.span("yend")[0]
        return rv

    def loc_ystart(self):
        if self.match.group("ystart"):
            rv = self.get_comment_text_loc()
            rv.col_end = rv.col_start + (self.match.span("ystart")[1] - 1)
            rv.col_start += self.match.span("ystart")[0]
            return rv
        else:
            return self.loc_yend()

    def set_parent(self, n_parent):
        assert isinstance(n_parent, Docstring)
        super().set_parent(n_parent)


class Docstring(Node):
    def __init__(self, copyright_regex):
        super().__init__()
        assert isinstance(copyright_regex, str)
        self.l_comments = []
        self.re_copyright = re.compile(copyright_regex)

        self.copyright_info = []

    def loc(self):
        if self.l_comments:
            return self.l_comments[0].location
        else:
            return self.n_parent.loc()

    def add_comment(self, t_comment):
        assert isinstance(t_comment, MATLAB_Token)
        assert t_comment.kind == "COMMENT"
        assert t_comment.first_in_line
        if self.l_comments:
            assert self.l_comments[-1].location.line < t_comment.location.line

        # Do not add block comment braces
        if t_comment.block_comment and t_comment.value in ("{", "}"):
            return

        self.l_comments.append(t_comment)
        t_comment.ast_link = self

        match = self.re_copyright.search(t_comment.value)
        if match:
            self.copyright_info.append(Copyright_Info(self, t_comment, match))

    def set_parent(self, n_parent):
        assert isinstance(n_parent, (Definition,
                                     Compilation_Unit))
        super().set_parent(n_parent)

    def get_all_copyright_holders(self):
        return set(n_info.get_org()
                   for n_info in self.copyright_info)

    def all_copyright_in_one_block(self, entities=None):
        """ Check if all copyright statements are next to each other """
        assert entities is None or isinstance(entities, set)

        lines = sorted(info.t_comment.location.line
                       for info in self.copyright_info
                       if entities is None or info.get_org() in entities)
        old_line = None
        for line_no in lines:
            if old_line is not None and line_no - old_line > 1:
                return False
            old_line = line_no

        return True

    def final_line(self):
        """ Returns a tuple identifying the final line of the docstring

        The tuple contains two values:
          * A boolean, indicating if we deal with a block comment
          * An int >= 0, indicating where to add a new line which would
            extend the docstring

        Returns the pen-ultimate line if the ending comment is a
        closing block comment.

        The only case we have a blank docstring is if we have a
        compilation unit docstring, in which case we'd return 0.
        """

        if not self.l_comments:
            return False, 0
        elif self.l_comments[-1].block_comment:
            return True, max(1, self.l_comments[-1].location.line)
        else:
            return False, self.l_comments[-1].location.line

    def guess_docstring_offset(self):
        """ Guesses the internal offset used for the docstring

        For example:
          % POTATO makes a potato
          %   This adds a potato

        Here the internal offset would be 3. The heuristic is not great
        right now, I'll improve it as I get bug reports :)
        """
        offsets = {}
        # OK, there is a minor bug here with tabs, but MH Style should
        # have fixed your code already.
        for t_comment in self.l_comments[1:]:
            rstripped_comment = t_comment.get_unstripped_comment().rstrip()
            offset = len(re.match("^ *", rstripped_comment).group(0))
            if offset:
                offsets[offset] = offsets.get(offset, 0) + 1

        if offsets:
            return min(offsets)
        elif self.l_comments:
            rstripped_comment = self.l_comments[0].get_unstripped_comment()
            return len(re.match("^ *", rstripped_comment).group(0))
        else:
            return 1


class Function_Signature(Node):
    def __init__(self):
        super().__init__()

        self.n_name = None
        # (Simple dotted) name of the function

        self.l_inputs = None
        # List of inputs

        self.l_outputs = None
        # List of outputs

        self.is_constructor = False
        # Set to true if this function signature refers to a
        # class constructor

    def loc(self):
        if self.n_name:
            return self.n_name.loc()
        else:
            raise ICE("cannot attach error to blank signature")

    def set_name(self, n_name):
        assert isinstance(n_name, Name)
        assert n_name.is_simple_dotted_name()

        self.n_name = n_name
        self.n_name.set_parent(self)

    def set_inputs(self, l_inputs):
        assert isinstance(l_inputs, list)
        for n in l_inputs:
            assert isinstance(n, Identifier), \
                str(n) + " is %s and not an Identifier" % n.__class__.__name__

        self.l_inputs  = l_inputs
        for n_input in self.l_inputs:
            n_input.set_parent(self)

    def set_outputs(self, l_outputs):
        assert isinstance(l_outputs, list)
        for n in l_outputs:
            assert isinstance(n, Identifier)

        self.l_outputs = l_outputs
        for n_output in self.l_outputs:
            n_output.set_parent(self)

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

    def sty_check_naming(self, mh, cfg):
        assert isinstance(mh, Message_Handler)
        assert isinstance(cfg, Config)

        # Check naming of parameters
        if cfg.active("naming_parameters"):
            for param in self.l_inputs + self.l_outputs:
                param.sty_check_naming(mh, cfg, "parameter")

        # We need to work out what we are. Options are:
        # 1. Class constructor (needs to follow class naming scheme)
        # 2. Ordinary function
        # 3. Nested function
        # 4. Class method (separate or otherwise)
        # 5. Naked signature in class as forward declaration

        if not cfg.active("naming_functions"):
            return

        n_fdef = self.n_parent

        if self.is_constructor:
            # This is the special case for class constructors: they
            # need to follow the naming scheme of classes, not methods
            if not isinstance(self.n_name, Identifier):
                raise ICE("class constructor with %s node as name" %
                          self.n_name.__class__.__name__)
            self.n_name.sty_check_naming(mh, cfg, "class")

        elif isinstance(n_fdef, Special_Block):
            # This is case 4: naked signature. Check as if it's
            # method.
            if not isinstance(self.n_name, Identifier):
                raise ICE("forward declaration with %s node as name" %
                          self.n_name.__class__.__name__)
            self.n_name.sty_check_naming(mh, cfg, "method")

        elif isinstance(n_fdef.n_parent, Function_Definition):
            # This is case 2: nested function
            if not isinstance(self.n_name, Identifier):
                raise ICE("nested function with %s node as name" %
                          self.n_name.__class__.__name__)
            self.n_name.sty_check_naming(mh, cfg, "nested")

        elif n_fdef.is_class_method():
            # This is case 3: class method. This is the only case we
            # can have a dotted name.
            if isinstance(self.n_name, Identifier):
                self.n_name.sty_check_naming(mh, cfg, "method")
            elif not isinstance(self.n_name, Selection):
                raise ICE("class method with %s node as name" %
                          self.n_name.__class__.__name__)
            else:
                self.n_name.n_field.sty_check_naming(mh, cfg, "method")

        else:
            # The remaining case is 1: normal function
            if not isinstance(self.n_name, Identifier):
                raise ICE("ordinary function with %s node as name" %
                          self.n_name.__class__.__name__)
            self.n_name.sty_check_naming(mh, cfg, "function")


class Sequence_Of_Statements(Node):
    def __init__(self, l_statements):
        super().__init__()
        assert isinstance(l_statements, list)
        for statement in l_statements:
            assert isinstance(statement, (Pragma, Statement))

        self.l_statements = l_statements
        for n_statement in self.l_statements:
            n_statement.set_parent(self)
        # The list of statements

    def prepend_pragmas(self, l_pragmas):
        assert isinstance(l_pragmas, list)
        for n_pragma in l_pragmas:
            assert isinstance(n_pragma, Pragma)

        self.l_statements = l_pragmas + self.l_statements
        for n_pragma in l_pragmas:
            n_pragma.set_parent(self)

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

    For example (Access = protected) or in 2021a (foo(x=y))
    """
    def __init__(self, n_name):
        super().__init__()
        assert isinstance(n_name, Identifier)

        self.n_name = n_name
        self.n_name.set_parent(self)
        # The name

        self.t_eq = None
        # The (optional) =

        self.n_value = None
        # The (optional) value

    def loc(self):
        return self.n_name.loc()

    def set_value(self, t_eq, n_value):
        assert isinstance(t_eq, MATLAB_Token)
        assert t_eq.kind == "ASSIGNMENT"
        assert isinstance(n_value, Expression)

        self.t_eq = t_eq
        self.t_eq.set_ast(self)

        self.n_value = n_value
        self.n_value.set_parent(self)

    def set_parent(self, n_parent):
        assert isinstance(n_parent, (Special_Block,
                                     Class_Definition,
                                     Reference))
        # Usually appears on the special blocks, but can also appear
        # directly on a classdef. Since 2021a it can appear in
        # function argument lists as well (which are initially parsed
        # as references).
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
    def __init__(self, t_kw):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value in ("properties",
                                                         "methods",
                                                         "events",
                                                         "enumeration",
                                                         "arguments")

        self.t_kw = t_kw
        self.t_kw.set_ast(self)
        # The token (which we also use to distinguish between the 5
        # different kinds of special block).

        self.l_attr = []
        # An optional list of attributes that applies to all items in
        # the block.

        self.l_items = []
        # List of items in this block

    def loc(self):
        return self.t_kw.location

    def set_attributes(self, l_attr):
        assert isinstance(l_attr, list)
        for n_attr in l_attr:
            assert isinstance(n_attr, Name_Value_Pair)

        self.l_attr = l_attr
        for n_attr in self.l_attr:
            n_attr.set_parent(self)

    def get_attribute(self, name):
        assert isinstance(name, str)

        for n_nv_pair in self.l_attr:
            if str(n_nv_pair.n_name) == name:
                return n_nv_pair
        return None

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

    def add_delegation(self, n_cons):
        assert isinstance(n_cons, Argument_Validation_Delegation)
        assert self.kind() == "arguments"
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
    def __init__(self):
        super().__init__()

        self.n_name = None
        # The entity name we refer to. This one is *not* optional.

        self.l_dim_constraint = []
        # List of optional dimension constraints. Must either be 0 or
        # more than 2. These are (integral) number/colon tokens and
        # not expressions.
        #
        # TODO: Validate that numbers are integral and convert to
        # python integers, discarding the tokens

        self.n_class_name = None
        # An optional class name our entity must fit

        self.l_fun_constraint = []
        # An optional list of functional constraints our entity must
        # meet.

        self.n_default_value = None
        # An optional default value expression

    def loc(self):
        if self.n_name:
            return self.n_name.loc()
        else:
            raise ICE("cannot attach error to blank entity constraints")

    def set_name(self, n_name):
        assert isinstance(n_name, Name)

        self.n_name = n_name
        self.n_name.set_parent(self)

    def set_dimension_constraints(self, l_dim_constraint):
        assert isinstance(l_dim_constraint, list)
        assert len(l_dim_constraint) >= 2
        for n_dim_constraint in l_dim_constraint:
            assert isinstance(n_dim_constraint, MATLAB_Token)
            assert n_dim_constraint.kind in ("NUMBER", "COLON")

        self.l_dim_constraint = l_dim_constraint
        for t_dim_constraint in self.l_dim_constraint:
            t_dim_constraint.set_ast(self)

    def set_class_constraint(self, n_class_name):
        assert isinstance(n_class_name, Name)

        self.n_class_name = n_class_name
        self.n_class_name.set_parent(self)

    def add_functional_constraint(self, n_fun_constraint):
        assert isinstance(n_fun_constraint, Name)

        n_fun_constraint.set_parent(self)
        self.l_fun_constraint.append(n_fun_constraint)

    def set_default_value(self, n_default_value):
        assert isinstance(n_default_value, Expression)

        self.n_default_value = n_default_value
        self.n_default_value.set_parent(self)

    def set_parent(self, n_parent):
        assert isinstance(n_parent, Special_Block)
        assert n_parent.kind() in ("properties", "arguments")
        super().set_parent(n_parent)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_name.visit(self, function, "Name")
        if self.n_class_name:
            self.n_class_name.visit(self, function, "Class")
        self._visit_list(self.l_fun_constraint, function, "Functions")
        if self.n_default_value:
            self.n_default_value.visit(self, function, "Default")
        self._visit_end(parent, function, relation)


class Argument_Validation_Delegation(Node):
    """ AST for a the .? special syntax found inside argument blocks.
    """
    def __init__(self, t_op):
        super().__init__()
        assert isinstance(t_op, MATLAB_Token) and t_op.kind == "NVP_DELEGATE"

        self.t_op = t_op
        self.t_op.set_ast(self)
        # The .? token

        self.n_name = None
        # The entity name we refer to.

        self.n_class_name = None
        # The name of the class we delegate validation to

    def loc(self):
        return self.t_op.location

    def set_name(self, n_name):
        assert isinstance(n_name, Name)

        self.n_name = n_name
        self.n_name.set_parent(self)

    def set_class_name(self, n_class_name):
        assert isinstance(n_class_name, Name)

        self.n_class_name = n_class_name
        self.n_class_name.set_parent(self)

    def set_parent(self, n_parent):
        assert isinstance(n_parent, Special_Block)
        assert n_parent.kind() == "arguments"
        super().set_parent(n_parent)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_name.visit(self, function, "Name")
        self.n_class_name.visit(self, function, "Class")
        self._visit_end(parent, function, relation)


class Class_Enumeration(Node):
    """ AST for enumeration literal/constructors inside classdefs """
    def __init__(self, n_name):
        super().__init__()
        assert isinstance(n_name, Identifier)

        self.n_name = n_name
        self.n_name.set_parent(self)
        # Name to introduce enumeration literal

        self.l_args = []
        # Parameters for class constructor to build this literal

    def loc(self):
        return self.n_name.loc()

    def add_argument(self, n_argument):
        isinstance(n_argument, Expression)

        self.l_args.append(n_argument)
        n_argument.set_parent(self)

    def set_parent(self, n_parent):
        assert isinstance(n_parent, Special_Block)
        assert n_parent.kind() == "enumeration"
        super().set_parent(n_parent)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_name.visit(self, function, "Name")
        self._visit_list(self.l_args, function, "Arguments")
        self._visit_end(parent, function, relation)

    def sty_check_naming(self, mh, cfg):
        assert isinstance(mh, Message_Handler)
        assert isinstance(cfg, Config)

        if cfg.active("naming_enumerations"):
            self.n_name.sty_check_naming(mh, cfg, "enumeration")


class Action(Node):
    """ AST node for actions in if or switch statements. """
    def __init__(self, t_kw):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD"
        assert t_kw.value in ("if", "elseif", "else", "case", "otherwise")

        self.t_kw = t_kw
        self.t_kw.set_ast(self)
        # The token to classify this action

        self.n_expr = None
        # An optional guard

        self.n_body = None
        # The body

    def loc(self):
        return self.t_kw.location

    def set_expression(self, n_expr):
        assert self.t_kw.value not in ("else", "otherwise")
        assert isinstance(n_expr, Expression)

        self.n_expr = n_expr
        self.n_expr.set_parent(self)

    def set_body(self, n_body):
        assert isinstance(n_body, Sequence_Of_Statements)

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
            self.n_expr.visit(self, function, "Guard")
        self.n_body.visit(self, function, "Body")
        self._visit_end(parent, function, relation)


class Row(Node):
    """ AST for matrix or cell array rows. """

    # Open question: are empty rows allowed?

    def __init__(self):
        super().__init__()

        self.l_items = []
        # Members of this row

    def loc(self):
        raise ICE("cannot attach error to matrix/cell rows")

    def set_parent(self, n_parent):
        assert isinstance(n_parent, Row_List)
        super().set_parent(n_parent)

    def add_item(self, n_item):
        assert isinstance(n_item, Expression)

        n_item.set_parent(self)
        self.l_items.append(n_item)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self._visit_list(self.l_items, function, "Items")
        self._visit_end(parent, function, relation)

    def is_empty(self):
        return not bool(self.l_items)


class Row_List(Node):
    """ AST for matrix or cell contents. """

    def __init__(self):
        super().__init__()

        self.l_items = []
        # List of rows

    def loc(self):
        raise ICE("cannot attach error to matrix/cell contents")

    def set_parent(self, n_parent):
        assert isinstance(n_parent, (Matrix_Expression,
                                     Cell_Expression))
        super().set_parent(n_parent)

    def add_item(self, n_item):
        assert isinstance(n_item, Row)

        n_item.set_parent(self)
        self.l_items.append(n_item)

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
    def __init__(self, n_ident):
        super().__init__()
        assert isinstance(n_ident, Name)

        self.n_ident = n_ident
        self.n_ident.set_parent(self)
        # An identifier

        self.l_args = None
        # A list of parameters or indices. This is set later so that
        # separating tokens can be correctly attached.

    def loc(self):
        return self.n_ident.loc()

    def set_arguments(self, l_args):
        assert isinstance(l_args, list)
        for n_arg in l_args:
            # Note that a NV pair imples that this reference will be a
            # function call. This is a dumb MATLAB 2021a feature that
            # actually provides a pair of arguments, an identifier
            # transformed a la command form into a string; and another
            # argument.
            assert isinstance(n_arg, (Expression, Name_Value_Pair))

        self.l_args = l_args
        for n_arg in self.l_args:
            n_arg.set_parent(self)

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
    def __init__(self, n_ident):
        super().__init__()
        assert isinstance(n_ident, Name)

        self.n_ident = n_ident
        self.n_ident.set_parent(self)
        # An identifier

        self.l_args = []
        # A list of indices

    def loc(self):
        return self.n_ident.loc()

    def add_argument(self, n_arg):
        assert isinstance(n_arg, Expression)

        self.l_args.append(n_arg)
        n_arg.set_parent(self)

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
            (t_ident.kind == "KEYWORD" and t_ident.value == "import") or \
            (t_ident.kind == "KEYWORD" and t_ident.value == "arguments") or \
            t_ident.kind == "BANG"

        self.t_ident = t_ident
        self.t_ident.set_ast(self)
        # The token

    def loc(self):
        return self.t_ident.location

    def __str__(self):
        if self.t_ident.kind == "BANG":
            return "system"
        else:
            return self.t_ident.value

    def is_simple_dotted_name(self):
        return self.t_ident.kind in ("IDENTIFIER", "KEYWORD")

    def sty_check_naming(self, mh, cfg, kind):
        assert isinstance(mh, Message_Handler)
        assert isinstance(cfg, Config)

        regex = cfg.style_config["regex_" + kind + "_name"]
        if not re.match("^(" + regex + ")$", self.t_ident.value):
            mh.style_issue(self.t_ident.location,
                           "violates naming scheme for %s" % kind)

    def sty_check_builtin_shadow(self, mh, cfg):
        assert isinstance(mh, Message_Handler)
        assert isinstance(cfg, Config)

        if self.t_ident.value in HIGH_IMPACT_BUILTIN_FUNCTIONS:
            mh.check(self.t_ident.location,
                     "redefining this builtin is very naughty")


class Selection(Name):
    def __init__(self, t_selection, n_prefix, n_field):
        super().__init__()
        assert isinstance(t_selection, MATLAB_Token)
        assert t_selection.kind == "SELECTION"
        assert isinstance(n_prefix, Name)
        assert isinstance(n_field, Identifier)

        self.t_selection = t_selection
        self.t_selection.set_ast(self)
        # The . token

        self.n_prefix = n_prefix
        self.n_prefix.set_parent(self)
        # The stuff befor the .

        self.n_field = n_field
        self.n_field.set_parent(self)
        # The stuff after the .

    def loc(self):
        return self.t_selection.location

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_prefix.visit(self, function, "Prefix")
        self.n_field.visit(self, function, "Field")
        self._visit_end(parent, function, relation)

    def __str__(self):
        return "%s.%s" % (self.n_prefix, self.n_field)

    def is_simple_dotted_name(self):
        return self.n_prefix.is_simple_dotted_name()


class Dynamic_Selection(Name):
    def __init__(self, t_selection, n_prefix, n_field):
        super().__init__()
        assert isinstance(t_selection, MATLAB_Token)
        assert t_selection.kind == "SELECTION"
        assert isinstance(n_prefix, Name)
        assert isinstance(n_field, Expression)

        self.t_selection = t_selection
        self.t_selection.set_ast(self)
        # The token for .

        self.n_prefix = n_prefix
        self.n_prefix.set_parent(self)
        # The stuff befor the .

        self.n_field = n_field
        self.n_field.set_parent(self)
        # The stuff in the brackets after the .

    def loc(self):
        return self.t_selection.location

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
        self.t_at.set_ast(self)
        # The token for @

        self.n_prefix = n_prefix
        self.n_prefix.set_parent(self)
        # Stuff before the @

        self.n_reference = n_reference
        self.n_reference.set_parent(self)
        # Stuff after the @

    def loc(self):
        return self.t_at.location

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
    def __init__(self, t_for):
        super().__init__()
        assert isinstance(t_for, MATLAB_Token)
        assert t_for.kind == "KEYWORD" and t_for.value in ("for",
                                                           "parfor")

        self.t_for = t_for
        self.t_for.set_ast(self)
        # The token for the for or parfor

        self.n_ident = None
        # The name of the iterator

        self.n_body = None
        # The body for the loop

    def loc(self):
        return self.t_for.location

    def set_ident(self, n_ident):
        assert isinstance(n_ident, Identifier)

        self.n_ident = n_ident
        self.n_ident.set_parent(self)

    def set_body(self, n_body):
        assert isinstance(n_body, Sequence_Of_Statements)

        self.n_body = n_body
        self.n_body.set_parent(self)

    def visit(self, parent, function, relation):
        raise ICE("reached visit procedure for abstract base class for"
                  " for-loops")


class General_For_Statement(For_Loop_Statement):
    def __init__(self, t_for):
        super().__init__(t_for)
        assert t_for.kind == "KEYWORD" and t_for.value == "for"

        self.n_expr = None
        # An expression returning some kind of matrix which defines
        # our loop bounds

    def set_expression(self, n_expr):
        assert isinstance(n_expr, Expression)

        self.n_expr = n_expr
        self.n_expr.set_parent(self)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_ident.visit(self, function, "Identifier")
        self.n_expr.visit(self, function, "Expression")
        self.n_body.visit(self, function, "Body")
        self._visit_end(parent, function, relation)


class Parallel_For_Statement(For_Loop_Statement):
    def __init__(self, t_for):
        super().__init__(t_for)
        assert t_for.kind == "KEYWORD" and t_for.value == "parfor"

        self.n_range = None
        # The range expression for the loop bounds

        self.n_workers = None
        # An optional indication of how work is distributed.

    def set_range(self, n_range):
        assert isinstance(n_range, Range_Expression)

        self.n_range = n_range
        self.n_range.set_parent(self)

    def set_workers(self, n_workers):
        assert isinstance(n_workers, Expression)

        self.n_workers = n_workers
        self.n_workers.set_parent(self)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_ident.visit(self, function, "Identifier")
        self.n_range.visit(self, function, "Range")
        if self.n_workers:
            self.n_workers.visit(self, function, "Workers")
        self.n_body.visit(self, function, "Body")
        self._visit_end(parent, function, relation)


class While_Statement(Compound_Statement):
    def __init__(self, t_while, n_guard):
        super().__init__()
        assert isinstance(t_while, MATLAB_Token)
        assert t_while.kind == "KEYWORD" and t_while.value == "while"
        assert isinstance(n_guard, Expression)

        self.t_while = t_while
        self.t_while.set_ast(self)
        # The token for while

        self.n_guard = n_guard
        self.n_guard.set_parent(self)
        # The guard expression

        self.n_body = None
        # The loop body

    def loc(self):
        return self.t_while.location

    def set_body(self, n_body):
        assert isinstance(n_body, Sequence_Of_Statements)

        self.n_body = n_body
        self.n_body.set_parent(self)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_guard.visit(self, function, "Guard")
        self.n_body.visit(self, function, "Body")
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

    def loc(self):
        return self.l_actions[0].loc()

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self._visit_list(self.l_actions, function, "Action")
        self._visit_end(parent, function, relation)


class Switch_Statement(Compound_Statement):
    def __init__(self, t_kw, n_switch_expr):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value == "switch"
        assert isinstance(n_switch_expr, Expression)

        self.t_kw = t_kw
        self.t_kw.set_ast(self)
        # The token for 'switch'

        self.n_expr = n_switch_expr
        self.n_expr.set_parent(self)
        # The expression in the switch statement itself

        self.l_actions = []
        # List of actions. Must be at least one. Case actions followed
        # by up to one otherwise action.

        self.has_otherwise = False
        # Cache if we have an otherwise or not.

    def loc(self):
        return self.t_kw.location

    def add_action(self, n_action):
        assert isinstance(n_action, Action)
        assert n_action.kind() in ("case", "otherwise")
        assert not self.has_otherwise

        n_action.set_parent(self)
        self.l_actions.append(n_action)
        if n_action.kind() == "otherwise":
            self.has_otherwise = True

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_expr.visit(self, function, "Guard")
        self._visit_list(self.l_actions, function, "Action")
        self._visit_end(parent, function, relation)


class Try_Statement(Compound_Statement):
    def __init__(self, t_try):
        super().__init__()
        assert isinstance(t_try, MATLAB_Token)
        assert t_try.kind == "KEYWORD" and t_try.value == "try"

        self.t_try = t_try
        self.t_try.set_ast(self)
        # The token for try

        self.t_catch = None
        # The optional token for catch

        self.n_ident = None
        # An optional identifier that names the caught exception.

        self.n_body = None
        # The body of the try block

        self.n_handler = None
        # An optional body for the catch block. If absent then the
        # semantics are to catch and ignore any exceptions, and resume
        # execution with the statement following this block.

    def loc(self):
        return self.t_try.location

    def set_body(self, n_body):
        assert isinstance(n_body, Sequence_Of_Statements)

        self.n_body = n_body
        self.n_body.set_parent(self)

    def set_handler_body(self, t_catch, n_handler):
        assert t_catch.kind == "KEYWORD" and t_catch.value == "catch"
        assert isinstance(n_handler, Sequence_Of_Statements)

        self.t_catch = t_catch
        self.t_catch.set_ast(self)
        self.n_handler = n_handler
        self.n_handler.set_parent(self)

    def set_ident(self, n_ident):
        assert isinstance(n_ident, Identifier)

        self.n_ident = n_ident
        self.n_ident.set_parent(self)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_body.visit(self, function, "Body")
        if self.n_ident:
            self.n_ident.visit(self, function, "Identifier")
        if self.n_handler:
            self.n_handler.visit(self, function, "Handler")
        self._visit_end(parent, function, relation)


class SPMD_Statement(Compound_Statement):
    def __init__(self, t_spmd):
        super().__init__()
        assert isinstance(t_spmd, MATLAB_Token)
        assert t_spmd.kind == "KEYWORD" and t_spmd.value == "spmd"

        self.t_spmd = t_spmd
        self.t_spmd.set_ast(self)
        # The token for the spmd keyword

        self.n_body = None
        # The body

    def loc(self):
        return self.t_spmd.location

    def set_body(self, n_body):
        assert isinstance(n_body, Sequence_Of_Statements)

        self.n_body = n_body
        self.n_body.set_parent(self)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_body.visit(self, function, "Body")
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
        self.t_eq.set_ast(self)
        # The token for the =

        self.n_lhs = n_lhs
        self.n_lhs.set_parent(self)
        # The target name of the assignment

        self.n_rhs = n_rhs
        self.n_rhs.set_parent(self)
        # The expression to assign

    def loc(self):
        return self.t_eq.location

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_lhs.visit(self, function, "LHS")
        self.n_rhs.visit(self, function, "RHS")
        self._visit_end(parent, function, relation)


class Compound_Assignment_Statement(Simple_Statement):
    # TODO: Rewrite single targets to Simple_Assignment_Statement
    def __init__(self):
        super().__init__()

        self.t_eq = None
        # The token for the =

        self.l_lhs = None
        # The list of assignment targets.

        self.n_rhs = None
        # The expression to assign. Must be a function call that
        # returns multiple outputs. We can't check it now (during
        # parsing), it will be checked during semantic analysis.

    def loc(self):
        if self.t_eq:
            return self.t_eq.location
        else:
            raise ICE("cannot attach error to blank compound assignment")

    def set_token_eq(self, t_eq):
        assert isinstance(t_eq, MATLAB_Token)
        assert t_eq.kind == "ASSIGNMENT"

        self.t_eq = t_eq
        self.t_eq.set_ast(self)

    def set_targets(self, l_lhs):
        assert isinstance(l_lhs, list)
        assert len(l_lhs) >= 1
        for n_lhs in l_lhs:
            assert isinstance(n_lhs, Name)

        self.l_lhs = l_lhs
        for n_target in self.l_lhs:
            n_target.set_parent(self)

    def set_expression(self, n_rhs):
        assert isinstance(n_rhs, Expression)

        self.n_rhs = n_rhs
        self.n_rhs.set_parent(self)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self._visit_list(self.l_lhs, function, "LHS")
        self.n_rhs.visit(self, function, "RHS")
        self._visit_end(parent, function, relation)


class Naked_Expression_Statement(Simple_Statement):
    def __init__(self, n_expr):
        super().__init__()
        assert isinstance(n_expr, Expression)

        self.n_expr = n_expr
        self.n_expr.set_parent(self)
        # The expression

    def loc(self):
        return self.n_expr.loc()

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_expr.visit(self, function, "Expression")
        self._visit_end(parent, function, relation)


class Return_Statement(Simple_Statement):
    def __init__(self, t_kw):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value == "return"

        self.t_kw = t_kw
        self.t_kw.set_ast(self)
        # The token for return

    def loc(self):
        return self.t_kw.location


class Break_Statement(Simple_Statement):
    def __init__(self, t_kw):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value == "break"

        self.t_kw = t_kw
        self.t_kw.set_ast(self)
        # The token for break

    def loc(self):
        return self.t_kw.location


class Continue_Statement(Simple_Statement):
    def __init__(self, t_kw):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value == "continue"

        self.t_kw = t_kw
        self.t_kw.set_ast(self)
        # The token for continue

    def loc(self):
        return self.t_kw.location


class Global_Statement(Simple_Statement):
    def __init__(self, t_kw):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value == "global"

        self.t_kw = t_kw
        self.t_kw.set_ast(self)
        # The token for global

        self.l_names = []
        # List of names from the special global namespace

    def loc(self):
        return self.t_kw.location

    def add_name(self, n_name):
        assert isinstance(n_name, Identifier)

        n_name.set_parent(self)
        self.l_names.append(n_name)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self._visit_list(self.l_names, function, "Names")
        self._visit_end(parent, function, relation)


class Persistent_Statement(Simple_Statement):
    def __init__(self, t_kw):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value == "persistent"

        self.t_kw = t_kw
        self.t_kw.set_ast(self)
        # The token for persistent

        self.l_names = []
        # List of identifiers to make persistent

    def loc(self):
        return self.t_kw.location

    def add_name(self, n_name):
        assert isinstance(n_name, Identifier)

        n_name.set_parent(self)
        self.l_names.append(n_name)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self._visit_list(self.l_names, function, "Names")
        self._visit_end(parent, function, relation)


class Import_Statement(Simple_Statement):
    def __init__(self, t_kw):
        super().__init__()
        assert isinstance(t_kw, MATLAB_Token)
        assert t_kw.kind == "KEYWORD" and t_kw.value == "import"

        self.t_kw = t_kw
        self.t_kw.set_ast(self)
        # The token for import

        self.l_chain = None
        # The tokens for the namespace to import. Will be identifiers,
        # followed by an optional operator (.*).

    def loc(self):
        return self.t_kw.location

    def set_chain(self, l_chain):
        assert isinstance(l_chain, list)
        for t_item in l_chain:
            assert isinstance(t_item, MATLAB_Token)
            assert t_item.kind == "IDENTIFIER" or \
                (t_item.kind == "OPERATOR" and t_item.value == ".*")

        self.l_chain = l_chain
        for t_item in self.l_chain:
            t_item.set_ast(self)

    def get_chain_strings(self):
        return [t.value if t.kind == "IDENTIFIER" else "*"
                for t in self.l_chain]


class Tag_Pragma(Pragma):
    def __init__(self, t_pragma, t_kind, l_tags):
        super().__init__(t_pragma, t_kind)
        assert isinstance(l_tags, list)
        assert len(l_tags) >= 1
        for t_tag in l_tags:
            assert t_tag.kind == "STRING"
            t_tag.set_ast(self)

        self.l_tags = l_tags
        # The list of tags

    def get_tags(self):
        return {t_tag.value for t_tag in self.l_tags}


class Justification_Pragma(Pragma):
    def __init__(self, t_pragma, t_kind, t_tool):
        super().__init__(t_pragma, t_kind)
        assert isinstance(t_tool, MATLAB_Token)
        assert t_tool.kind == "IDENTIFIER"

        self.t_tool = t_tool
        self.t_tool.set_ast(self)
        # The tool. Will always be 'metric' in this case. This will
        # move out to general justification pragmas once we get there.

        self.applies = False
        # Is set to true by mh_metric if this pragma successfully
        # justifies a metrics violation. That way we can do a tree
        # walk at the end and complain about all pragmas that don't
        # actually do something.


class Metric_Justification_Pragma(Justification_Pragma):
    def __init__(self, t_pragma, t_kind, t_tool, t_metric, n_reason,
                 ticket_regex):
        super().__init__(t_pragma, t_kind, t_tool)
        assert isinstance(t_tool, MATLAB_Token)
        assert t_tool.kind == "IDENTIFIER" and t_tool.value == "metric"
        assert isinstance(t_metric, MATLAB_Token)
        assert t_metric.kind == "STRING"
        assert isinstance(n_reason, (String_Literal, Binary_Operation))
        assert isinstance(ticket_regex, str)

        self.t_metric = t_metric
        self.t_metric.set_ast(self)
        # A string to identify the metric

        self.n_reason = n_reason
        self.n_reason.set_parent(self)
        # The reason why this deviation is OK. Currently just a string
        # literal, but can be a string expression in the future.

        if ticket_regex:
            # re.findall does not work if there are groups in the
            # user-supplied regular expression. See #174.
            self.tickets = frozenset(match.group(0)
                                     for match in re.finditer(ticket_regex,
                                                              self.reason()))
        else:
            self.tickets = frozenset()

    def metric(self):
        return self.t_metric.value

    def reason(self):
        return self.n_reason.evaluate_static_string_expression()

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_reason.visit(self, function, "Reason")
        self._visit_end(parent, function, relation)


##############################################################################
# Literals
##############################################################################


class Number_Literal(Literal):
    def __init__(self, t_value):
        super().__init__()
        assert isinstance(t_value, MATLAB_Token)
        assert t_value.kind == "NUMBER"

        self.t_value = t_value
        self.t_value.set_ast(self)
        # The token for the number literal

    def __str__(self):
        return self.t_value.value

    def loc(self):
        return self.t_value.location


class Char_Array_Literal(Literal):
    def __init__(self, t_string):
        super().__init__()
        assert isinstance(t_string, MATLAB_Token)
        assert t_string.kind in ("CARRAY", "BANG")

        self.t_string = t_string
        self.t_string.set_ast(self)
        # The token for the char array literal. It can also be a bang
        # token so we can use it as a char array argument to system()
        # when re-writing ! directives to a function call to system.

    def __str__(self):
        return "'" + self.t_string.value + "'"

    def loc(self):
        return self.t_string.location


class String_Literal(Literal):
    def __init__(self, t_string):
        super().__init__()
        assert isinstance(t_string, MATLAB_Token)
        assert t_string.kind == "STRING"

        self.t_string = t_string
        self.t_string.set_ast(self)
        # The token for the string literal.

    def __str__(self):
        return '"' + self.t_string.value + '"'

    def loc(self):
        return self.t_string.location

    def evaluate_static_string_expression(self):
        return self.t_string.value


##############################################################################
# Expressions
##############################################################################


class Reshape(Expression):
    def __init__(self, t_colon):
        super().__init__()
        assert isinstance(t_colon, MATLAB_Token)
        assert t_colon.kind == "COLON"

        self.t_colon = t_colon
        self.t_colon.set_ast(self)
        # The token for :

    def loc(self):
        return self.t_colon.location

    def set_parent(self, n_parent):
        assert isinstance(n_parent, (Reference,
                                     Cell_Reference))
        # This can only appear in very specific situations. it is not
        # to be confused by a Range_Expression.
        super().set_parent(n_parent)

    def __str__(self):
        return ":"


class Range_Expression(Expression):
    def __init__(self,
                 n_first, t_first_colon, n_last,
                 t_second_colon=None, n_stride=None):
        super().__init__()
        assert isinstance(n_first, Expression)
        assert isinstance(n_last, Expression)
        assert isinstance(t_first_colon, MATLAB_Token)
        if t_second_colon:
            assert isinstance(t_second_colon, MATLAB_Token)
            assert t_second_colon.kind == "COLON"
            assert isinstance(n_stride, Expression)
        else:
            assert n_stride is None

        self.t_first_colon = t_first_colon
        self.t_first_colon.set_ast(self)
        # The first colon

        self.t_second_colon = t_second_colon
        if self.t_second_colon:
            self.t_second_colon.set_ast(self)
        # The optional second colon

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

    def loc(self):
        return self.t_first_colon.location

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
    def __init__(self, t_open):
        super().__init__()
        assert isinstance(t_open, MATLAB_Token)
        assert t_open.kind == "M_BRA"

        self.t_open = t_open
        self.t_open.set_ast(self)
        self.t_close = None
        # The tokens for [ and ]

        self.n_content = None
        # Matrix rows

    def loc(self):
        return self.t_open.location

    def set_content(self, n_content):
        assert isinstance(n_content, Row_List)

        n_content.set_parent(self)
        self.n_content = n_content

    def set_closing_bracket(self, t_close):
        assert isinstance(t_close, MATLAB_Token)
        assert t_close.kind == "M_KET"

        self.t_close = t_close
        self.t_close.set_ast(self)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_content.visit(self, function, "Content")
        self._visit_end(parent, function, relation)


class Cell_Expression(Expression):
    def __init__(self, t_open):
        super().__init__()
        assert isinstance(t_open, MATLAB_Token)
        assert t_open.kind == "C_BRA"

        self.t_open = t_open
        self.t_open.set_ast(self)
        self.t_close = None
        # The tokens for { and }

        self.n_content = None

    def loc(self):
        return self.t_open.location

    def set_content(self, n_content):
        assert isinstance(n_content, Row_List)

        n_content.set_parent(self)
        self.n_content = n_content

    def set_closing_bracket(self, t_close):
        assert isinstance(t_close, MATLAB_Token)
        assert t_close.kind == "C_KET"

        self.t_close = t_close
        self.t_close.set_ast(self)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_content.visit(self, function, "Content")
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

    def loc(self):
        return self.n_name.loc()

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        if self.variant != "escape":
            self.n_name.visit(self, function, "Name")
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
        self.t_op.set_ast(self)
        # The token for the operator symbol

        self.n_expr = n_expr
        self.n_expr.set_parent(self)
        # The expression

        # To support the style checker we flag that this operator is
        # unary.
        self.t_op.fix.unary_operator = True

    def loc(self):
        return self.t_op.location

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_expr.visit(self, function, "Expression")
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
        self.t_op.set_ast(self)
        # The token for the operator symbol

        self.n_lhs = n_lhs
        self.n_lhs.set_parent(self)
        # The left-hand expression

        self.n_rhs = n_rhs
        self.n_rhs.set_parent(self)
        # The right-hand expression

        # To support the style checker we flag that this operator is
        # unary.
        self.t_op.fix.binary_operator = True

    def loc(self):
        return self.t_op.location

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_lhs.visit(self, function, "LHS")
        self.n_rhs.visit(self, function, "RHS")
        self._visit_end(parent, function, relation)

    def __str__(self):
        return "(%s %s %s)" % (self.n_lhs, self.t_op.value, self.n_rhs)

    def evaluate_static_string_expression(self):
        if self.t_op.value == "+":
            return (self.n_lhs.evaluate_static_string_expression() +
                    self.n_rhs.evaluate_static_string_expression())
        else:
            return super().evaluate_static_string_expression()


class Binary_Logical_Operation(Binary_Operation):
    def __init__(self, precedence, t_op, short_circuit, n_lhs, n_rhs):
        # In some contexts a normal & or | takes on short-circuit
        # semantics. Specifically inside an "if" or "while"
        # guard. Hence we can overwrite the behaviour for & or | here
        # with the short_circuit flag.
        super().__init__(precedence, t_op, n_lhs, n_rhs)
        assert t_op.value in ("&", "&&", "|", "||")
        assert short_circuit if t_op.value in ("&&", "||") else True

        self.short_circuit = short_circuit


class Lambda_Function(Expression):
    def __init__(self, t_at):
        super().__init__()
        assert isinstance(t_at, MATLAB_Token)
        assert t_at.kind == "AT"

        self.t_at = t_at
        self.t_at.set_ast(self)
        # The token for @

        self.l_parameters = []
        # Names for the parameters for our lambda function

        self.n_body = None
        # The expression

    def loc(self):
        return self.t_at.location

    def add_parameter(self, n_parameter):
        assert isinstance(n_parameter, Identifier)

        self.l_parameters.append(n_parameter)
        n_parameter.set_parent(self)

    def set_body(self, n_body):
        assert isinstance(n_body, Expression)
        self.n_body = n_body
        self.n_body.set_parent(self)

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self._visit_list(self.l_parameters, function, "Parameters")
        self.n_body.visit(self, function, "Body")
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
        self.t_at.set_ast(self)
        # The token for @

        self.n_name = n_name
        self.n_name.set_parent(self)
        # The (simple dotted) name of the function we point to

    def loc(self):
        return self.t_at.location

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_name.visit(self, function, "Name")
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
        self.t_mc.set_ast(self)
        # The token for ?

        self.n_name = n_name
        self.n_name.set_parent(self)
        # The (simple dotted) name of a class

    def loc(self):
        return self.t_mc.location

    def visit(self, parent, function, relation):
        self._visit(parent, function, relation)
        self.n_name.visit(self, function, "Name")
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
            if isinstance(node, Binary_Logical_Operation):
                self.write("Short-Circuit: %s" % node.short_circuit)
        elif isinstance(node, Import_Statement):
            self.write_head(node.__class__.__name__ +
                            " for " +
                            ".".join(node.get_chain_strings()),
                            relation)
        elif isinstance(node, Metric_Justification_Pragma):
            self.write_head(node.__class__.__name__ +
                            " for %s" % node.t_metric.value,
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
        if node.n_class_name:
            dot(fd, node, "class", node.n_class_name)
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
