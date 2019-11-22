#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2019, Zenuity AB                              ##
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

import os
from copy import deepcopy

from m_lexer import MATLAB_Lexer
from errors import mh, ICE, Error, Location

CONFIG_FILENAME = "miss_hit.cfg"

DEFAULT = {
    "enable"           : True,
    "file_length"      : 1000,
    "line_length"      : 80,
    "tab_width"        : 4,
    "copyright_entity" : set()
}

CONFIG_TREE = {}


class Config_Parser:
    def __init__(self, config_file):
        self.filename = config_file
        self.lexer = MATLAB_Lexer(self.filename)
        self.ct = None
        self.nt = None
        self.next()

    def next(self):
        self.ct = self.nt
        self.nt = self.lexer.token()

        while self.nt:
            # Skip comments
            while self.nt and self.nt.kind == "COMMENT":
                self.nt = self.lexer.token()

            # Join new-lines
            if (self.nt and
                self.ct and
                self.nt.kind == "NEWLINE" and
                self.ct.kind == "NEWLINE"):
                self.nt = self.lexer.token()
            else:
                break

    def match(self, kind, value=None):
        self.next()
        if self.ct is None:
            mh.error(Location(self.lexer.filename),
                     "expected %s, reached EOF instead" % kind)
        elif self.ct.kind != kind:
            mh.error(self.ct.location,
                     "expected %s, found %s instead" % (kind, self.ct.kind))
        elif value and self.ct.value() != value:
            mh.error(self.ct.location,
                     "expected %s(%s), found %s(%s) instead" %
                     (kind, value, self.ct.kind, self.ct.value()))

    def match_eof(self):
        self.next()
        if self.ct is not None:
            mh.error(self.ct.location,
                     "expected end of file, found %s instead" % self.ct.kind)

    def peek(self, kind, value=None):
        if self.nt and self.nt.kind == kind:
            if value is None:
                return True
            else:
                return self.nt.value() == value
        else:
            return False
        self.ct

    def parse_file(self, cfg):
        while self.nt:
            if self.nt.kind == "NEWLINE":
                self.match("NEWLINE")
            else:
                self.match("IDENTIFIER")
                t_key = self.ct
                key = self.ct.value()
                self.match("COLON")

                if key not in cfg:
                    mh.error(t_key.location,
                             "unknown option %s" % key)

                elif isinstance(cfg[key], int):
                    self.match("NUMBER")
                    try:
                        value = int(self.ct.value())
                    except ValueError:
                        mh.error(self.ct.location,
                                 "%s option requires an integer" % key)

                elif isinstance(cfg[key], bool):
                    self.match("NUMBER")
                    if self.ct.value() in ("0", "1"):
                        value = self.ct.value() == "1"
                    else:
                        mh.error(self.ct.location,
                                 "boolean option %s requires 0 or 1" % key)

                elif isinstance(cfg[key], set):
                    self.match("STRING")
                    value = self.ct.value()

                if self.nt:
                    self.match("NEWLINE")
                else:
                    self.match_eof()

                if isinstance(cfg[key], set):
                    cfg[key].add(value)
                else:
                    cfg[key] = value


def load_config(cfg_file, cfg):
    assert isinstance(cfg_file, str)
    assert os.path.isfile(cfg_file)
    assert isinstance(cfg, dict)

    try:
        mh.register_file(cfg_file)
        p = Config_Parser(cfg_file)
        p.parse_file(cfg)
        # Now that we have parsed the file, we should remove it again
        # from the list of files known to the error handler
        mh.unregister_file(cfg_file)
    except Error:
        mh.print_summary_and_exit()


def register_tree(dirname):
    assert isinstance(dirname, str)
    assert os.path.isdir(dirname)
    assert dirname == os.path.abspath(dirname)

    def register_parent(dirname):
        if dirname in CONFIG_TREE:
            return

        # Stop if we reach the root filesystem or a .git directory
        parent = os.path.dirname(dirname)
        is_root = (parent == dirname or
                   os.path.isdir(os.path.join(dirname, ".git")))

        if not is_root:
            register_parent(parent)
            CONFIG_TREE[parent]["children"].add(dirname)

        CONFIG_TREE[dirname] = {
            "children"   : set(),
            "subtree"    : False,
            "has_config" : os.path.isfile(os.path.join(dirname,
                                                       CONFIG_FILENAME)),
            "root"       : is_root,
            "parent"     : None if is_root else parent
        }

    def register_subtree(dirname):
        if CONFIG_TREE[dirname]["subtree"]:
            return

        CONFIG_TREE[dirname]["children"] = set([
            os.path.join(dirname, d)
            for d in os.listdir(dirname)
            if os.path.isdir(os.path.join(dirname, d))])

        for child in CONFIG_TREE[dirname]["children"]:
            register_tree(child)

        CONFIG_TREE[dirname]["subtree"] = True

    register_parent(dirname)
    register_subtree(dirname)


def build_config_tree(cmdline_options):
    roots = [d for d in CONFIG_TREE if CONFIG_TREE[d]["root"]]

    def merge_command_line(cfg):
        # Overwrite with options from the command-line
        if cmdline_options.line_length:
            cfg["line_length"] = options.line_length
        if cmdline_options.file_length:
            cfg["file_length"] = options.file_length
        if cmdline_options.tab_width:
            cfg["tab_width"] = options.tab_width
        if cmdline_options.copyright_entity:
            cfg["copyright_entity"] = set(options.copyright_entity)

    def build(node, allow_root=False):
        if CONFIG_TREE[node]["root"]:
            if allow_root:
                CONFIG_TREE[node]["config"] = deepcopy(DEFAULT)
                merge_command_line(CONFIG_TREE[node]["config"])
            else:
                return
        else:
            parent = CONFIG_TREE[node]["parent"]
            parent_config = CONFIG_TREE[parent]["config"]
            if CONFIG_TREE[node]["has_config"]:
                CONFIG_TREE[node]["config"] = deepcopy(parent_config)
            else:
                CONFIG_TREE[node]["config"] = parent_config

        if CONFIG_TREE[node]["has_config"]:
            load_config(os.path.join(node, CONFIG_FILENAME),
                        CONFIG_TREE[node]["config"])
            merge_command_line(CONFIG_TREE[node]["config"])

        for child in CONFIG_TREE[node]["children"]:
            build(child)

    for root in roots:
        build(root, True)

def get_config(filename):
    d = os.path.dirname(os.path.abspath(filename))

    if d not in CONFIG_TREE:
        raise ICE("expected %s to be in configuration tree" % d)

    return CONFIG_TREE[d]["config"]
