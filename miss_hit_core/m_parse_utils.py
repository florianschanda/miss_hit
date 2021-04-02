#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2021, Florian Schanda                         ##
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

from miss_hit_core.errors import Message_Handler
from miss_hit_core.m_ast import *
from miss_hit_core.m_lexer import Token_Buffer


def parse_docstrings(mh, cfg, parse_tree, tbuf):
    """ Post process parse tree, attaching docstrings to primary entities """
    assert isinstance(mh, Message_Handler)
    assert isinstance(parse_tree, Compilation_Unit)
    assert isinstance(tbuf, Token_Buffer)

    # The compilation unit's docstring are the leading comments in the
    # file (if any).

    approaching_docstring = False
    in_docstring = tbuf.tokens and tbuf.tokens[0].kind == "COMMENT"
    if in_docstring:
        ast_node = Docstring(cfg.style_config["copyright_regex"])
        parse_tree.set_docstring(ast_node)
    else:
        ast_node = None

    for token in tbuf.tokens:
        # Recognise docstrings
        if approaching_docstring:
            # In this mode we keep eating tokens until we get to the
            # first comment token, that is a _new_ statement. This
            # deals with line continuations.
            if token.first_in_statement:
                if token.kind == "COMMENT":
                    in_docstring = True
                approaching_docstring = False

        if in_docstring:
            # In this mode we eat comments and newlines until we get
            # to a non-comment token, or more than one newline.
            if token.kind == "COMMENT":
                ast_node.add_comment(token)
            elif token.kind == "NEWLINE" and token.value.count("\n") == 1:
                pass
            else:
                in_docstring = False

        if token.kind == "KEYWORD" and token.value in ("function",
                                                       "classdef"):
            # Recognise function docstrings
            approaching_docstring = True
            if token.ast_link is None:
                raise ICE("keyword is not linked to AST")
            elif not isinstance(token.ast_link, Definition):
                raise ICE("AST link is %s and not a Definition" %
                          token.ast_link.__class__.__name__)
            ast_node = Docstring(cfg.style_config["copyright_regex"])
            token.ast_link.set_docstring(ast_node)
