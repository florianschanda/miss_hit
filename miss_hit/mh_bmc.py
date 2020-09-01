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

import json

from miss_hit_core import command_line
from miss_hit_core import work_package
from miss_hit_core import m_ast
from miss_hit_core.errors import Message_Handler, Error
from miss_hit_core.m_lexer import MATLAB_Lexer
from miss_hit_core.m_parser import MATLAB_Parser

from miss_hit import goto_ast


def compile_function(mh, gst, n_fdef):
    assert isinstance(mh, Message_Handler)
    assert isinstance(gst, goto_ast.GOTO_Symbol_Table)
    assert isinstance(n_fdef, m_ast.Function_Definition)

    function_name = str(n_fdef.n_sig.n_name)

    sym_fn_type = goto_ast.Code_Type()

    # Create names for the function inputs
    inputs = {}
    for n_param in n_fdef.n_sig.l_inputs:
        pretty_name = str(n_param)
        mangled_name = "::".join([function_name, "in", pretty_name])

        sym = goto_ast.Symbol(mangled_name, pretty_name)
        sym.is_parameter = True
        sym.value = goto_ast.Irep("nil")
        sym.typ = goto_ast.SignedBV_Type(32)
        sym.location = n_param.loc()
        inputs[pretty_name] = mangled_name
        gst.add_symbol(sym)

        sym_fn_type.add_parameter(goto_ast.Parameter(mangled_name, sym.typ))

    # Create names for the function outputs. Goto supports void
    # functions and functions with a single return. Right now we only
    # deal with non-void functions as that maps more or less 1:1.
    outputs = {}
    if len(n_fdef.n_sig.l_outputs) != 1:
        mh.error(n_fdef.loc(),
                 "mh_bmc supports only functions returning exactly one value")
    for n_param in n_fdef.n_sig.l_outputs:
        pretty_name = str(n_param)
        mangled_name = "::".join([function_name, "out", pretty_name])

        sym = goto_ast.Symbol(mangled_name, pretty_name)
        sym.value = goto_ast.Irep("nil")
        sym.typ = goto_ast.SignedBV_Type(32)
        sym.location = n_param.loc()
        outputs[pretty_name] = mangled_name
        gst.add_symbol(sym)

        sym_fn_type.set_return_type(sym.typ)

    # Complain about bits that we don't support yet
    for n_vld in n_fdef.l_validation:
        mh.error(n_vld.loc(), "not supported yet")
    for n_nst in n_fdef.l_nested:
        mh.error(n_nst.loc(), "nested function not supported yet")

    # Translate body
    sym = goto_ast.Symbol(function_name)
    sym.typ = sym_fn_type
    sym.value = goto_ast.Code_Block()

    # Add to the symbol table
    gst.add_symbol(sym)


def compile_file(mh, n_tree):
    assert isinstance(mh, Message_Handler)
    assert isinstance(n_tree, m_ast.Node)

    if not isinstance(n_tree, m_ast.Function_File):
        mh.error(n_tree.loc(),
                 "mh_bmc only supports function files right now")

    gst = goto_ast.GOTO_Symbol_Table()

    # Compile all functions
    for n_fdef in n_tree.l_functions:
        compile_function(mh, gst, n_fdef)

    return gst


class MH_BMC_Result(work_package.Result):
    def __init__(self, wp):
        super().__init__(wp, True)


class MH_BMC(command_line.MISS_HIT_Back_End):
    def __init__(self, _):
        super().__init__("MH Bounded Model Checker")

    @classmethod
    def process_wp(cls, wp):
        # Create lexer
        lexer = MATLAB_Lexer(wp.mh,
                             wp.get_content(),
                             wp.filename,
                             wp.blockname)
        if wp.cfg.octave:
            lexer.set_octave_mode()
        if not wp.cfg.pragmas:
            lexer.process_pragmas = False
        if len(lexer.text.strip()) == 0:
            return MH_BMC_Result(wp)

        # Create parse tree and translate
        try:
            parser = MATLAB_Parser(wp.mh, lexer, wp.cfg)
            n_tree = parser.parse_file()
            gst = compile_file(wp.mh, n_tree)
        except Error:
            return MH_BMC_Result(wp)

        new_filename = wp.filename.replace(".m", ".json_symtab")
        with open(new_filename, "w") as fd:
            json.dump(gst.to_json(), fd, indent=2)
        wp.mh.info(n_tree.loc(),
                   "wrote goto symbol table to %s" % new_filename)

        return MH_BMC_Result(wp)


def main_handler():
    clp = command_line.create_basic_clp()
    options = command_line.parse_args(clp)

    mh = Message_Handler("bmc")
    mh.show_context = not options.brief
    mh.show_style   = False
    mh.show_checks  = False
    mh.autofix      = False

    bmc_backend = MH_BMC(options)
    command_line.execute(mh, options, {}, bmc_backend)


def main():
    command_line.ice_handler(main_handler)


if __name__ == "__main__":
    main()
