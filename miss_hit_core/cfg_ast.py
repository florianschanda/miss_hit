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

# Tiny AST for the MISS_HIT configuration files

import os
from glob import glob

from abc import ABCMeta, abstractmethod

from miss_hit_core.m_ast import MATLAB_Token
from miss_hit_core.errors import Location, Message_Handler, ICE
from miss_hit_core.config import (Config,
                                  Boolean_Style_Configuration,
                                  Integer_Style_Configuration,
                                  String_Style_Configuration,
                                  Set_Style_Configuration,
                                  STYLE_RULES, STYLE_CONFIGURATION, METRICS)


class Node(metaclass=ABCMeta):
    def __init__(self):
        self.n_parent = None

    def set_parent(self, n_parent):
        assert isinstance(n_parent, Node)
        self.n_parent = n_parent

    @abstractmethod
    def dump(self):
        pass


class Config_File(Node):
    def __init__(self):
        super().__init__()
        self.l_items = []
        self.is_project_root = False

    def __iter__(self):
        return self.l_items.__iter__()

    def add_item(self, n_item):
        assert isinstance(n_item, Config_Item)

        self.l_items.append(n_item)
        n_item.set_parent(self)

        if isinstance(n_item, Project_Root):
            self.is_project_root = True

    def dump(self):
        print("MISS_HIT configuration file")
        for n_item in self.l_items:
            n_item.dump()


class Config_Item(Node):
    @abstractmethod
    def evaluate(self, mh, config):
        assert isinstance(mh, Message_Handler)
        assert isinstance(config, Config)


class Style_Application(Config_Item):
    # Turning style rules on or off
    def __init__(self, rule_name, enabled):
        super().__init__()
        assert isinstance(rule_name, str)
        assert rule_name in STYLE_RULES
        assert isinstance(enabled, bool)

        self.rule_name = rule_name
        self.enabled   = enabled

        self.the_rule = STYLE_RULES[self.rule_name]

    def dump(self):
        print("  Style application for %s" % self.rule_name)
        print("    Enabled: %s" % self.enabled)

    def evaluate(self, mh, config):
        assert isinstance(mh, Message_Handler)
        assert isinstance(config, Config)

        if self.enabled:
            config.style_rules.add(self.rule_name)
        elif self.rule_name in config.style_rules:
            config.style_rules.remove(self.rule_name)


class Style_Configuration(Config_Item):
    # Configuring specific style rules
    def __init__(self, config_name, value):
        super().__init__()
        assert isinstance(config_name, str)
        assert config_name in STYLE_CONFIGURATION

        self.config_name = config_name
        self.value       = value

        self.the_config = STYLE_CONFIGURATION[self.config_name]

    def dump(self):
        print("  Style configuration %s" % self.config_name)
        print("    Value: %s" % self.value)

    def evaluate(self, mh, config):
        assert isinstance(mh, Message_Handler)
        assert isinstance(config, Config)

        if isinstance(self.the_config, Integer_Style_Configuration):
            config.style_config[self.config_name] = self.value

        elif isinstance(self.the_config, Boolean_Style_Configuration):
            config.style_config[self.config_name] = self.value

        elif isinstance(self.the_config, String_Style_Configuration):
            # Also covers regex configuration
            config.style_config[self.config_name] = self.value

        elif isinstance(self.the_config, Set_Style_Configuration):
            config.style_config[self.config_name].add(self.value)

        else:
            raise ICE("unexpected config kind %s" %
                      self.the_config.__class__.__name__)


class Metric_Limit(Config_Item):
    # Turning metrics on/off and enforcing limits
    def __init__(self, metric_name, enabled, limit=None):
        super().__init__()
        assert isinstance(metric_name, str)
        assert metric_name in METRICS or metric_name == "*"
        assert isinstance(enabled, bool)
        assert isinstance(limit, int) or limit is None

        self.metric_name = metric_name
        self.enabled     = enabled
        self.limit       = limit

    def dump(self):
        print("  Metric limit for %s" % self.metric_name)
        if not self.enabled:
            print("    Metric: ignore")
        elif self.limit is not None:
            print("    Metric: limit to %i" % self.limit)
        else:
            print("    Metric: report")

    def evaluate(self, mh, config):
        assert isinstance(mh, Message_Handler)
        assert isinstance(config, Config)

        if self.metric_name == "*":
            if self.enabled:
                config.enabled_metrics = set(METRICS)
            else:
                config.enabled_metrics = set()
            config.metric_limits = {}

        elif self.enabled:
            config.enabled_metrics.add(self.metric_name)
            if self.limit is None:
                if self.metric_name in config.metric_limits:
                    del config.metric_limits[self.metric_name]
            else:
                config.metric_limits[self.metric_name] = self.limit

        else:
            if self.metric_name in config.enabled_metrics:
                config.enabled_metrics.remove(self.metric_name)
            if self.metric_name in config.metric_limits:
                del config.metric_limits[self.metric_name]


class Activation(Config_Item):
    # Turn MISS_HIT on or off
    def __init__(self, enabled):
        super().__init__()
        assert isinstance(enabled, bool)
        self.enabled = enabled

    def dump(self):
        if self.enabled:
            print("  Global MH Activation")
        else:
            print("  Global MH Disable")

    def evaluate(self, mh, config):
        assert isinstance(mh, Message_Handler)
        assert isinstance(config, Config)

        config.enabled = self.enabled


class Directory_Exclusion(Config_Item):
    # Completely remove one or more directories from consideration
    def __init__(self):
        super().__init__()
        self.directories = set()

    def __iter__(self):
        return self.directories.__iter__()

    def add_directory(self, directory):
        assert isinstance(directory, str)
        self.directories.add(directory)

    def dump(self):
        print("  Directory exclusion")
        for dirname in sorted(self.directories):
            # We normalize these to use / so we don't get
            # windows/linux diffs in the testsuite
            print("    Excluded: %s" % dirname.replace("\\", "/"))

    def evaluate(self, mh, config):
        raise ICE("logic error - called evaluate() for exclude_dir")


class Project_Root(Config_Item):
    # Indicates a project root (via config file)
    def dump(self):
        print("  MISS_HIT project root")

    def evaluate(self, mh, config):
        raise ICE("logic error - called evaluate() for project_root")


class Octave_Mode(Config_Item):
    # Toggle octave mode. For now this is just on or off, but in the
    # future it could be a 'both' mode as well.
    def __init__(self, enabled):
        super().__init__()
        assert isinstance(enabled, bool)
        self.enabled = enabled

    def dump(self):
        if self.enabled:
            print("  Dialect: Octave")
        else:
            print("  Dialect: MATLAB")

    def evaluate(self, mh, config):
        assert isinstance(mh, Message_Handler)
        assert isinstance(config, Config)

        config.octave = self.enabled


class Path_List:
    def __init__(self, root):
        assert isinstance(root, str)
        self.root = root

        self.s_paths = set()
        self.l_paths = []

    def add_path(self, mh, t_path):
        assert isinstance(t_path, MATLAB_Token)

        names = [os.path.relpath(path, self.root)
                 for path in glob(os.path.join(self.root,
                                               t_path.value))]

        if names:
            for name in sorted(names):
                if name in self.s_paths:
                    mh.config_error(t_path.location,
                                    "duplicate/overlapping path %s" % name)
                elif not os.path.isdir(os.path.join(self.root, name)):
                    mh.config_error(t_path.location,
                                    "%s is not a directory" % name)

                self.s_paths.add(name)
                self.l_paths.append(name)
        else:
            # Python docs say "possibly empty list", not sure how
            # though. If you don't match, it seems to return the
            # wild-card verbatim.
            mh.config_error(t_path.location,
                            "does not exist")

    def get_path(self):
        if self.l_paths:
            # Our path list is just what is specified, in order.
            return [os.path.join(self.root, path)
                    for path in self.l_paths]

        else:
            # If we do not have any paths specified, so the only path
            # is the item's root.
            return [self.root]


class Project_Directive(Config_Item):
    def __init__(self, location, directory, name):
        super().__init__()

        assert isinstance(location, Location)
        self.location = location
        # Location if we need to raise errors

        assert isinstance(directory, str)
        assert os.path.isdir(directory)
        self.directory = directory
        # The directory this item is rooted in

        assert isinstance(name, str)
        self.name = name
        # Name (also what will be used in the symbol table)

    def evaluate(self, mh, config):
        raise ICE("logic error - called evaluate() for project directive")

    @abstractmethod
    def validate(self, mh, symbol_table):
        pass

    @abstractmethod
    def get_source_path(self):
        # Get the actual PATH for source code for this library. This
        # decides the search order for user-defined functions and
        # classes.
        pass

    @abstractmethod
    def get_test_path(self):
        # Get the actual PATH for tests for this library. This decides
        # the search order for user-defined functions and classes.
        pass


class Library_Declaration(Project_Directive):
    def __init__(self, location, directory, name=None):
        if name is None:
            name = os.path.basename(os.path.abspath(directory))
        super().__init__(location, directory, name)

        self.path_list_source = Path_List(directory)
        self.path_list_test   = Path_List(directory)
        self.is_global        = False

    def __str__(self):
        return "Library(%s)" % self.name

    def add_source_path(self, mh, t_path):
        self.path_list_source.add_path(mh, t_path)

    def add_test_path(self, mh, t_path):
        self.path_list_test.add_path(mh, t_path)

    def dump(self):
        print("  Library Declaration (%s)" % self.name)
        for t_path in self.path_list_source.l_paths:
            print("    Source Path: %s" % t_path.value)
        for t_path in self.path_list_test.l_paths:
            print("    Test   Path: %s" % t_path.value)

    def validate(self, mh, symbol_table):
        pass

    def get_source_path(self):
        return self.path_list_source.get_path()

    def get_test_path(self):
        return self.path_list_test.get_path()

    def set_global(self):
        self.is_global = True


class Entrypoint_Declaration(Project_Directive):
    def __init__(self, location, directory, name):
        super().__init__(location, directory, name)

        self.path_list_source = Path_List(directory)
        self.path_list_test   = Path_List(directory)

        self.l_libraries = []
        self.s_libraries = set()
        # Libraries that this entry-point depends on. Initially this
        # is a list of tokens, but after validation is replaced with a
        # list of Library_Declaration nodes.

    def add_source_path(self, mh, t_path):
        self.path_list_source.add_path(mh, t_path)

    def add_test_path(self, mh, t_path):
        self.path_list_test.add_path(mh, t_path)

    def add_lib_dependency(self, mh, t_lib):
        assert isinstance(t_lib, MATLAB_Token)

        if t_lib.value in self.s_libraries:
            mh.config_error(t_lib.location,
                            "duplicate library")

        self.s_libraries.add(t_lib.value)
        self.l_libraries.append(t_lib)

    def dump(self):
        print("  Entrypoint Declaration (%s)" % self.name)
        for t_path in self.path_list_source.l_paths:
            print("    Source Path: %s" % t_path.value)
        for t_path in self.path_list_test.l_paths:
            print("    Test   Path: %s" % t_path.value)
        for t_lib in self.l_libraries:
            print("    Requires library: %s" % t_lib)

    def validate(self, mh, symbol_table):
        resolved_library_list = []
        for t_lib in self.l_libraries:
            if t_lib.value not in symbol_table:
                mh.config_error(t_lib.location,
                                "cannot find library")
            else:
                resolved_library_list.append(symbol_table[t_lib.value])
        self.l_libraries = resolved_library_list

    def get_source_path(self):
        # We start with the directory this entry point is in.
        path = self.path_list_source.get_path()

        # And now add, in order, the libraries' paths
        for n_lib in self.l_libraries:
            path += n_lib.get_source_path()

        return path

    def get_test_path(self):
        # We start with the directory this entry point is in.
        path = self.path_list_test.get_path()

        # And now add, in order, the libraries' paths
        for n_lib in self.l_libraries:
            path += n_lib.get_test_path()

        return path
