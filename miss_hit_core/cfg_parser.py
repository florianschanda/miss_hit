#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2020-2021, Florian Schanda                    ##
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

# Simple parser (based on the MATLAB lexer) for our config file. Some
# reasoning this is based on the MATLAB lexer:
#   - increases complexity in the MATLAB lexer a bit, since it adds another
#     lexing mode
#   + we can re-use the error raising mechanism
#   + we don't have to implement a separate lexer
#   + we don't have to depend on e.g. PLY (which is not a bad thing, I love
#     PLY, but since we have zero dependencies right now this would be
#     a bit annoying)

import re
import difflib
import os.path
from copy import deepcopy

from miss_hit_core import m_lexer
from miss_hit_core.errors import ICE, Error, Location, Message_Handler
from miss_hit_core.config import (STYLE_RULES, STYLE_CONFIGURATION,
                                  METRICS,
                                  Boolean_Style_Configuration,
                                  Integer_Style_Configuration,
                                  Regex_Style_Configuration,
                                  Encoding_Style_Configuration,
                                  String_Style_Configuration,
                                  Choice_Style_Configuration,
                                  Set_Style_Configuration)
from miss_hit_core.cfg_ast import *


class Config_Parser:
    def __init__(self, mh, config_file):
        assert isinstance(mh, Message_Handler)
        assert isinstance(config_file, str)

        self.filename = config_file
        self.dirname = os.path.dirname(os.path.abspath(config_file))
        self.mh = mh

        self.mh.register_file(self.filename)
        with open(config_file, "r") as fd:
            content = fd.read()
        self.lexer = m_lexer.MATLAB_Lexer(mh, content, self.filename)
        self.lexer.set_config_file_mode()

        # pylint: disable=invalid-name
        self.ct = None
        self.nt = None
        # pylint: enable=invalid-name

        self.skip()

    ##########################################################################
    # Generic recursive descent parser support

    def skip(self):
        self.ct = self.nt
        self.nt = self.lexer.token()

        # Skip comments and newlines
        while self.nt and self.nt.kind in ("COMMENT", "NEWLINE"):
            self.nt = self.lexer.token()

    def match(self, kind, value=None):
        self.skip()
        if self.ct is None:
            self.mh.error(self.lexer.get_file_loc(),
                          "expected %s, reached EOF instead" % kind)
        elif self.ct.kind != kind:
            self.mh.error(self.ct.location,
                          "expected %s, found %s instead" % (kind,
                                                             self.ct.kind))
        elif value and self.ct.value != value:
            self.mh.error(self.ct.location,
                          "expected %s(%s), found %s(%s) instead" %
                          (kind, value, self.ct.kind, self.ct.value))

    def match_eof(self):
        self.skip()
        if self.ct is not None:
            self.mh.error(self.ct.location,
                          "expected end of file, found %s instead" %
                          self.ct.kind)

    def peek(self, kind, value=None):
        if self.nt and self.nt.kind == kind:
            if value is None:
                return True
            else:
                return self.nt.value == value
        else:
            return False

    def peek_eof(self):
        return self.nt is None

    ##########################################################################
    # Top-down parsing (main entry point is parse_config_file)

    def parse_config_file(self):
        n_file = Config_File()
        has_errors = False

        while not self.peek_eof():
            try:
                n_item = self.parse_config_item()
            except Error:
                # On errors, we skip tokens until we get to a
                # newline
                has_errors = True
                n_item = None
                while not self.peek_eof() and not self.nt.first_in_line:
                    self.skip()

            if n_item:
                n_file.add_item(n_item)

        self.match_eof()

        if has_errors:
            self.mh.error(Location(self.filename),
                          "config file contains errors")
            return None

        return n_file

    def parse_config_item(self):
        n_item = None

        if self.peek("IDENTIFIER", "metric"):
            n_item = self.parse_metric_limit()

        elif self.peek("IDENTIFIER", "enable"):
            n_item = self.parse_simple_enable()

        elif self.peek("IDENTIFIER", "enable_rule") or \
             self.peek("IDENTIFIER", "suppress_rule"):
            n_item = self.parse_style_application()

        elif self.peek("IDENTIFIER", "exclude_dir"):
            n_item = self.parse_directory_exclusion()

        elif self.peek("IDENTIFIER", "project_root"):
            n_item = self.parse_project_root()

        elif self.peek("IDENTIFIER", "octave"):
            n_item = self.parse_octave_mode()

        elif self.peek("IDENTIFIER", "entrypoint"):
            n_item = self.parse_entrypoint()

        elif self.peek("IDENTIFIER", "library"):
            n_item = self.parse_library()

        elif self.peek("KEYWORD", "global"):
            self.match("KEYWORD", "global")
            if self.peek("IDENTIFIER", "library"):
                n_item = self.parse_library()
                n_item.set_global()
            else:
                self.skip()
                self.mh.error(self.ct.location,
                              "expected library, found %s instead" %
                              (self.ct.kind))

        elif self.peek("IDENTIFIER"):
            n_item = self.parse_style_configuration()

        else:
            self.skip()
            self.mh.error(self.ct.location,
                          "expected valid config entry, found %s instead" %
                          (self.ct.kind))

        return n_item

    def parse_integer_number(self):
        self.match("NUMBER")
        try:
            value = int(self.ct.value)
        except ValueError:
            self.mh.error(self.ct.location, "expected an integer number")
        return value

    def parse_natural_number(self):
        value = self.parse_integer_number()
        if value < 0:
            self.mh.error(self.ct.location, "expected a natural number (>= 0)")
        return value

    def parse_string(self):
        self.match("STRING")
        return self.ct.value

    def parse_regex(self):
        value = self.parse_string()

        # We can use the Python regex module to sanity check it
        try:
            re.compile(value)
        except re.error as err:
            loc = deepcopy(self.ct.location)
            if err.colno is not None:
                loc.col_start += err.colno
                loc.col_end = loc.col_start

                self.mh.error(loc, err.msg)

        return value

    def parse_encoding(self):
        value = self.parse_string()

        # We can use the Python regex module to sanity check it
        try:
            "potato".encode(value)
        except LookupError:
            self.mh.error(self.ct.location, "not a valid encoding")

        return value

    def parse_boolean(self):
        if self.peek("NUMBER"):
            value = self.parse_integer_number()
            if value in (0, 1):
                return bool(value)
            else:
                self.mh.error(self.ct.location, "expected true or false")

        elif self.peek("IDENTIFIER"):
            self.match("IDENTIFIER")
            if self.ct.value == "true":
                return True
            elif self.ct.value == "false":
                return False
            else:
                self.mh.error(self.ct.location, "expected true or false")

        else:
            self.skip()
            self.mh.error(self.ct.location, "expected true or false")

    def parse_simple_enable(self):
        self.match("IDENTIFIER", "enable")
        self.match("COLON")
        value = self.parse_boolean()

        return Activation(value)

    def parse_style_application(self):
        self.match("IDENTIFIER")
        if self.ct.value == "enable_rule":
            enabled = True
        elif self.ct.value == "suppress_rule":
            enabled = False
        else:
            self.mh.error(self.ct.location,
                          "expected enable_rule or suppress_rule")

        self.match("COLON")

        self.match("STRING")
        rule_name = self.ct.value
        if rule_name not in STYLE_RULES:
            msg = "expected valid style rule name"
            suggestions = difflib.get_close_matches(rule_name,
                                                    list(STYLE_RULES),
                                                    n=1)
            if suggestions:
                msg += " (did you mean %s?)" % suggestions[0]
            self.mh.error(self.ct.location, msg)

        return Style_Application(rule_name, enabled)

    def parse_style_configuration(self):
        self.match("IDENTIFIER")
        config_name = self.ct.value
        if config_name not in STYLE_CONFIGURATION:
            msg = "expected valid style configuration name"
            suggestions = difflib.get_close_matches(config_name,
                                                    list(STYLE_CONFIGURATION),
                                                    n=1)
            if suggestions:
                msg += " (did you mean %s?)" % suggestions[0]
            self.mh.error(self.ct.location, msg)

        self.match("COLON")

        cfg_item = STYLE_CONFIGURATION[config_name]
        value = None
        if isinstance(cfg_item, Integer_Style_Configuration):
            value = self.parse_integer_number()
            if cfg_item.lower_limit is not None:
                if value < cfg_item.lower_limit:
                    self.mh.error(self.ct.location,
                                  "%s must be at least %i" %
                                  (config_name,
                                   cfg_item.lower_limit))
            if cfg_item.upper_limit is not None:
                if value > cfg_item.upper_limit:
                    self.mh.error(self.ct.location,
                                  "%s can be at most %i" %
                                  (config_name,
                                   cfg_item.upper_limit))

        elif isinstance(cfg_item, Regex_Style_Configuration):
            value = self.parse_regex()

        elif isinstance(cfg_item, Encoding_Style_Configuration):
            value = self.parse_encoding()

        elif isinstance(cfg_item, Set_Style_Configuration):
            value = self.parse_string()

        elif isinstance(cfg_item, String_Style_Configuration):
            value = self.parse_string()

            if isinstance(cfg_item, Choice_Style_Configuration):
                if value not in cfg_item.choices:
                    self.mh.error(self.ct.location,
                                  "must be one of %s" %
                                  " or ".join(cfg_item.choices))

        elif isinstance(cfg_item, Boolean_Style_Configuration):
            value = self.parse_boolean()

        else:
            raise ICE("unexpected cfg kind %s" % cfg_item.__class__.__name__)

        return Style_Configuration(config_name, value)

    def parse_directory_exclusion(self):
        self.match("IDENTIFIER", "exclude_dir")
        self.match("COLON")
        value = self.parse_string()

        if not os.path.exists(os.path.join(self.dirname, value)):
            self.mh.error(self.ct.location, "does not exist")
        elif not os.path.isdir(os.path.join(self.dirname, value)):
            self.mh.error(self.ct.location,
                          "is not a directory")
        elif os.path.basename(value) != value:
            self.mh.error(self.ct.location,
                          "must local (non-relative) directory")

        # TODO: Allow wildcards (see #5)

        rv = Directory_Exclusion()
        rv.add_directory(value)
        return rv

    def parse_metric_limit(self):
        self.match("IDENTIFIER", "metric")

        if self.peek("OPERATOR", "*"):
            self.match("OPERATOR", "*")
            metric_name = "*"

        else:
            metric_name = self.parse_string()
            if metric_name not in METRICS:
                msg = "expected valid code metric or '*'"
                suggestions = difflib.get_close_matches(metric_name,
                                                        list(METRICS),
                                                        n=1)
                if suggestions:
                    msg += " (did you mean %s?)" % suggestions[0]
                self.mh.error(self.ct.location, msg)

        self.match("COLON")

        if self.peek("IDENTIFIER", "disable"):
            self.match("IDENTIFIER", "disable")
            return Metric_Limit(metric_name, False)

        elif self.peek("IDENTIFIER", "report"):
            self.match("IDENTIFIER", "report")
            return Metric_Limit(metric_name, True)

        elif self.peek("IDENTIFIER", "limit"):
            self.match("IDENTIFIER", "limit")
            if metric_name == "*":
                self.mh.error(self.ct.location,
                              "cannot apply limit to all metrics")
            value = self.parse_natural_number()
            return Metric_Limit(metric_name, True, value)

        else:
            self.skip()
            if metric_name == "*":
                self.mh.error(self.ct.location,
                              "expected disable|report")
            else:
                self.mh.error(self.ct.location,
                              "expected disable|report|limit")

    def parse_project_root(self):
        self.match("IDENTIFIER", "project_root")
        return Project_Root()

    def parse_octave_mode(self):
        self.match("IDENTIFIER", "octave")
        self.match("COLON")
        value = self.parse_boolean()
        return Octave_Mode(value)

    def parse_entrypoint(self):
        self.match("IDENTIFIER", "entrypoint")
        self.match("STRING")
        rv = Entrypoint_Declaration(self.ct.location,
                                    self.dirname,
                                    self.ct.value)
        self.match("C_BRA")

        while not (self.peek("C_KET") or self.peek_eof()):
            if self.peek("IDENTIFIER", "libraries"):
                for t_lib in self.parse_lib_dependencies():
                    rv.add_lib_dependency(self.mh, t_lib)
            elif self.peek("IDENTIFIER", "paths"):
                self.match("IDENTIFIER", "paths")
                for t_path in self.parse_lib_paths():
                    rv.add_source_path(self.mh, t_path)
            elif self.peek("IDENTIFIER", "tests"):
                self.match("IDENTIFIER", "tests")
                for t_path in self.parse_lib_paths():
                    rv.add_test_path(self.mh, t_path)
            else:
                self.mh.error(self.nt.location,
                              "expected libraries|paths property")

        self.match("C_KET")
        return rv

    def parse_library(self):
        self.match("IDENTIFIER", "library")
        if self.peek("STRING"):
            self.match("STRING")
            name = self.ct.value
        else:
            name = None
        rv = Library_Declaration(self.ct.location,
                                 self.dirname,
                                 name)

        self.match("C_BRA")

        while not (self.peek("C_KET") or self.peek_eof()):
            if self.peek("IDENTIFIER", "paths"):
                self.match("IDENTIFIER", "paths")
                for t_path in self.parse_lib_paths():
                    rv.add_source_path(self.mh, t_path)
            elif self.peek("IDENTIFIER", "tests"):
                self.match("IDENTIFIER", "tests")
                for t_path in self.parse_lib_paths():
                    rv.add_test_path(self.mh, t_path)
            else:
                self.mh.error(self.nt.location,
                              "expected paths property")

        self.match("C_KET")
        return rv

    def parse_lib_dependencies(self):
        rv = []
        self.match("IDENTIFIER", "libraries")
        self.match("C_BRA")
        while self.peek("STRING"):
            self.match("STRING")
            rv.append(self.ct)
            if self.peek("COMMA"):
                self.match("COMMA")
            else:
                break
        self.match("C_KET")
        return rv

    def parse_lib_paths(self):
        rv = []
        self.match("C_BRA")
        while self.peek("STRING"):
            self.match("STRING")
            rv.append(self.ct)
            if self.peek("COMMA"):
                self.match("COMMA")
            else:
                break
        self.match("C_KET")
        return rv


def load_config(mh, filename):
    cfg_parser = Config_Parser(mh, os.path.relpath(filename))
    tree = cfg_parser.parse_config_file()
    mh.unregister_file(os.path.relpath(filename))
    return tree


def sanity_test(mh, filename, show_bt):
    # pylint: disable=import-outside-toplevel
    import traceback
    # pylint: enable=import-outside-toplevel

    try:
        tree = load_config(mh, filename)
        tree.dump()

    except Error:
        if show_bt:
            traceback.print_exc()

    except ICE as ice:
        if show_bt:
            traceback.print_exc()
        print("ICE:", ice.reason)


def cfg_parser_main():
    # pylint: disable=import-outside-toplevel
    from argparse import ArgumentParser
    # pylint: enable=import-outside-toplevel

    ap = ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--no-tb",
                    action="store_true",
                    default=False,
                    help="Do not show debug-style backtrace")
    options = ap.parse_args()

    mh = Message_Handler("debug")
    mh.sort_messages = False
    mh.colour = False

    sanity_test(mh, options.file,
                not options.no_tb)

    mh.summary_and_exit()


if __name__ == "__main__":
    cfg_parser_main()
