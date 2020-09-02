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

# This is a set of classes you can build a goto symbol table from. It
# really should be auto-generated, but there is no authoritive
# specification of the CBMC ireps. Hopefully there will be in the
# future.
#
# Be advised: this is extremely incomplete and only enough for the MVP
# for the MH BMC project. To be completed in the future.

from abc import ABCMeta, abstractmethod


class GOTO_Symbol_Table:
    def __init__(self):
        self.stab = {}

        # Add the special initialize function
        sym_init = Symbol("__CPROVER_initialize")
        sym_init.value = Irep("nil")
        sym_init.typ = Code_Type()
        self.add_symbol(sym_init)

    def add_symbol(self, sym):
        assert isinstance(sym, Symbol)
        assert sym.name not in self.stab
        self.stab[sym.name] = sym

    def to_json(self):
        return {"symbolTable" : {name: self.stab[name].to_json()
                                 for name in self.stab}}


class Node(metaclass=ABCMeta):
    @abstractmethod
    def to_json(self):
        pass


class Symbol(Node):
    # See CBMC, src/util/symbol.h
    def __init__(self, name, pretty_name=None):
        assert isinstance(name, str)
        assert isinstance(pretty_name, str) or pretty_name is None

        if pretty_name is None:
            pretty_name = name

        self.name = name
        # (str) The unique identifier

        self.typ = None
        # (irep, type) Type of symbol

        self.value = None
        # (irep, expr) Initial value of symbol

        self.location = None
        # (irep, sloc) Source code location of definition of symbol

        self.module = None
        # (str) Name of module the symbol belongs to

        self.base_name = pretty_name
        # (str) Base (non-scoped) name

        self.pretty_name = pretty_name
        # (str) Language-specific display name

        self.is_type = False
        self.is_macro = False
        self.is_exported = False
        self.is_input = False
        self.is_output = False
        self.is_state_var = False
        self.is_property = False
        # (bool) global use

        self.is_static_lifetime = False
        self.is_thread_locat = False
        self.is_lvalue = False
        self.is_file_lcoal = False
        self.is_extern = False
        self.is_volatile = False
        self.is_parameter = False
        self.is_auxiliary = False
        self.is_weak = False
        # (bool) ANSI-C

    def to_json(self):
        assert self.name is not None

        rv = {"name" : self.name,
              "mode" : "C"}
        # Setting C here is not a mistake; there is a bunch of
        # hard-coded options in CBMC and you can't just invent
        # something new from the outside.

        if self.typ is not None:
            rv["type"] = self.typ.to_json()

        if self.value is not None:
            rv["value"] = self.value.to_json()

        if self.location:
            # TODO: Source location
            pass

        if self.module:
            rv["module"] = self.module

        if self.base_name:
            rv["baseName"] = self.base_name

        if self.pretty_name:
            rv["prettyName"] = self.pretty_name

        if self.is_type:
            rv["isType"] = True
        if self.is_macro:
            rv["isMacro"] = True
        if self.is_exported:
            rv["isExported"] = True
        if self.is_input:
            rv["isInput"] = True
        if self.is_output:
            rv["isOutput"] = True
        if self.is_state_var:
            rv["isStateVar"] = True
        if self.is_property:
            rv["isProperty"] = True

        if self.is_static_lifetime:
            rv["isStaticLifetime"] = True
        if self.is_thread_locat:
            rv["isThreadLocal"] = True
        if self.is_lvalue:
            rv["isLvalue"] = True
        if self.is_file_lcoal:
            rv["isFileLocal"] = True
        if self.is_extern:
            rv["isExtern"] = True
        if self.is_volatile:
            rv["isVolatile"] = True
        if self.is_parameter:
            rv["isParameter"] = True
        if self.is_auxiliary:
            rv["isAuxiliary"] = True
        if self.is_weak:
            rv["isWeak"] = True

        return rv


class Irep(Node):
    def __init__(self, id_str):
        assert isinstance(id_str, str)
        self.id_str = id_str

        self.sub = []
        self.named_sub = {}

    def set_attribute(self, name, value):
        assert isinstance(name, str)
        assert isinstance(value, str)

        self.named_sub[name] = Irep(value)

    def to_json(self):
        rv = {"id" : self.id_str}
        if self.sub:
            rv["sub"] = [item.to_json() for item in self.sub]
        if self.named_sub:
            rv["namedSub"] = {k : self.named_sub[k].to_json()
                              for k in self.named_sub}
        return rv


##############################################################################
# From util/expr.h
##############################################################################

class Expr(Irep):
    def __init__(self, id_str, typ=None):
        assert isinstance(typ, Type) or typ is None
        super().__init__(id_str)

        if typ is not None:
            self.set_type(typ)

    def set_type(self, typ):
        assert isinstance(typ, Type)
        self.named_sub["type"] = typ

    def get_type(self):
        return self.named_sub["type"]


##############################################################################
# From util/type.h
##############################################################################

class Type(Irep):
    pass


class SignedBV_Type(Type):
    def __init__(self, width):
        assert isinstance(width, int)
        super().__init__("signedbv")
        self.set_attribute("width", str(width))


##############################################################################
# From util/std_types.h
##############################################################################

class Parameters(Expr):
    def __init__(self):
        super().__init__("")


class Parameter(Expr):
    def __init__(self, name, typ):
        assert isinstance(name, str)
        assert isinstance(typ, Type)
        super().__init__("parameter")

        self.set_attribute("#identifier", name)
        self.named_sub["type"] = typ


class Code_Type(Type):
    def __init__(self):
        super().__init__("code")
        self.named_sub["parameters"] = Parameters()
        self.named_sub["return_type"] = Irep("empty")

    def set_return_type(self, return_type):
        assert isinstance(return_type, Type)
        self.named_sub["return_type"] = return_type

    def add_parameter(self, parameter):
        assert isinstance(parameter, Parameter)
        self.named_sub["parameters"].sub.append(parameter)


##############################################################################
# From util/std_expr.h
##############################################################################

class Nullary_Expr(Expr):
    pass


class Multi_Ary_Expr(Expr):
    pass


class Constant_Expr(Expr):
    def __init__(self, typ, value):
        assert isinstance(value, str)
        super().__init__("constant", typ)
        self.set_attribute("value", value)


class Symbol_Expr(Nullary_Expr):
    def __init__(self, typ, name):
        assert isinstance(name, str)
        super().__init__("symbol", typ)
        self.set_attribute("identifier", name)


class Plus_Expr(Multi_Ary_Expr):
    def __init__(self, typ, ops):
        assert isinstance(ops, list)
        super().__init__("+", typ)
        for operand in ops:
            assert isinstance(operand, Expr)
            self.sub.append(operand)


##############################################################################
# From util/std_code.h
##############################################################################

class Code(Irep):
    def __init__(self):
        super().__init__("code")
        self.set_attribute("type", "empty")


class Code_Block(Code):
    def __init__(self):
        super().__init__()
        self.set_attribute("statement", "block")

    def add_statement(self, stmt):
        assert isinstance(stmt, Code)
        self.sub.append(stmt)


class Code_Expression(Code):
    def __init__(self, expr):
        assert isinstance(expr, Expr)
        super().__init__()
        self.set_attribute("statement", "expression")
        self.sub.append(expr)


class Side_Effect_Expr(Expr):
    def __init__(self, typ, kind):
        assert isinstance(kind, str)
        super().__init__("side_effect", typ)
        self.set_attribute("statement", kind)


class Side_Effect_Expr_Assign(Side_Effect_Expr):
    def __init__(self, typ, lhs, rhs):
        assert isinstance(lhs, Expr)
        assert isinstance(rhs, Expr)
        super().__init__(typ, "assign")
        self.sub.append(lhs)
        self.sub.append(rhs)


class Code_Return(Code):
    def __init__(self, value=None):
        assert isinstance(value, Expr) or value is None
        super().__init__()
        self.set_attribute("statement", "return")

        if value is not None:
            self.sub.append(value)


# class Code_Declaration(Code):
#     def __init__(self):
#         super().__init__()
#         self.set_attribute("statement", "decl")


def sanity_test():
    # pylint: disable=import-outside-toplevel
    import json
    from pprint import pprint

    sym_main = Symbol("main", "main")
    sym_main.value = Code_Block()
    sym_main.typ = Code_Type()
    sym_main.typ.set_return_type(SignedBV_Type(32))

    sym_init = Symbol("__CPROVER_initialize")
    sym_init.value = Irep("nil")
    sym_init.typ = Code_Type()

    stab = {"symbolTable" : {
        "__CPROVER_initialize" : sym_init.to_json(),
        "main" : sym_main.to_json(),
    }}

    pprint(stab)
    with open("sanity.json_symtab", "w") as fd:
        json.dump(stab, fd, indent=2)


if __name__ == "__main__":
    sanity_test()
