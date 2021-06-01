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

# Package for dealing with a configuration in a complex MATLAB project
#
# API is to call register_item for anything (dir or file) that we're
# supposed to analyse. This build a configuration tree, which can be
# accessed with get_config.

import os

from miss_hit_core.cfg_parser import load_config
from miss_hit_core.errors import ICE, Error, Location, Message_Handler
from miss_hit_core.cfg_ast import *

DEBUG_TRACE_TREE = False
# Enable to get spammed about where/how we build the config tree.

CONFIG_FILENAMES = ["miss_hit.cfg", ".miss_hit"]
# Valid config file names. Any directory is allowed at most one.

USE_DOT_GIT = False
# Consider a directory containing ".git" a project root. In the future
# this will be configurable through some global configuration
# mechanism.

tree = {}
# Our database for configuration

project_names = {}
# Our symbol table for project configuration


class Tree_Node:
    def __init__(self, project_root, config_files):
        assert isinstance(project_root, bool)
        assert isinstance(config_files, list)

        self.project_root      = project_root
        self.config_files      = config_files
        self.ast               = None
        self.config            = None
        self.subtree_included  = False
        self.excluded_children = set()

    def set_ast(self, ast):
        assert isinstance(ast, Config_File)
        self.ast = ast
        if self.ast.is_project_root:
            self.project_root = True


def register_project_name(mh, n_item):
    assert isinstance(n_item, (Library_Declaration,
                               Entrypoint_Declaration))

    if n_item.name in project_names:
        mh.config_error(n_item.location,
                        "duplicate definition, previous definition at %s" %
                        project_names[n_item.name].location.short_string())

    project_names[n_item.name] = n_item


def register_parent(mh, options, dirname):
    assert isinstance(dirname, str)
    parent_dirname = os.path.dirname(dirname)

    if dirname in tree:
        return

    if DEBUG_TRACE_TREE:
        print("RP: %s" % dirname)

    # Check for a ".git" directory. This would indicate we've found a
    # project root.
    if USE_DOT_GIT and os.path.isdir(os.path.join(dirname, ".git")):
        found_root = True

    # Check if we're at the top of the filesystem
    elif parent_dirname == dirname:
        found_root = True

    # Otherwise we probably continue up
    else:
        found_root = False

    # Check if we have a config file present
    config_files = []
    if not options.ignore_config:
        for cfg_filename in CONFIG_FILENAMES:
            if os.path.isfile(os.path.join(dirname, cfg_filename)):
                config_files.append(cfg_filename)

    tree[dirname] = Tree_Node(found_root, config_files)

    if len(config_files) > 1:
        mh.config_error(Location(os.path.relpath(dirname)),
                        "multiple config files found; cannot find project"
                        " root: please add a config file with the"
                        " 'project_root' directive")

    elif config_files:
        try:
            cfg_file_ast = load_config(mh,
                                       os.path.join(dirname, config_files[0]))
            tree[dirname].set_ast(cfg_file_ast)

        except Error:
            cfg_file_ast = None

        if cfg_file_ast is None:
            mh.config_error(Location(os.path.relpath(dirname)),
                            "cannot find project root because the config file"
                            " contains errors: please add a config file with"
                            " the 'project_root' directive")

    if not tree[dirname].project_root:
        register_parent(mh, options, parent_dirname)


def apply_config(mh, options, dirname, exclusions_only=False):
    assert isinstance(dirname, str)
    assert dirname in tree
    parent_dirname = os.path.dirname(dirname)

    node = tree[dirname]

    # We already have configuration applied here. Nothing to do.
    if node.config:
        return

    if DEBUG_TRACE_TREE:
        if node.project_root:
            trace_msg = "Applying root"
        else:
            trace_msg = "Applying"
        if exclusions_only:
            trace_msg += " exclusions"
        else:
            trace_msg += " config"
        trace_msg += " in %s" % dirname
        print(trace_msg)

    # Set up new config: either the default configuration, or inherit
    # from our parent. We only do this when we process the full
    # config.
    if not exclusions_only:
        if node.project_root:
            node.config = Config()
        else:
            node.config = Config(tree[parent_dirname].config)

    # If we have a config file AST, apply it now
    if node.ast:
        for n_item in node.ast:
            if isinstance(n_item, Directory_Exclusion):
                for edir in n_item:
                    if DEBUG_TRACE_TREE:
                        print("  > Excluding %s" % edir)
                    excluded_path = os.path.join(dirname, edir)
                    node.excluded_children.add(edir)
                    if excluded_path in tree:
                        tree[excluded_path].project_root = True

            elif exclusions_only:
                continue

            elif isinstance(n_item, Project_Root):
                # This will have been previously applied. We can ignore
                # this.
                pass

            elif isinstance(n_item, (Library_Declaration,
                                     Entrypoint_Declaration)):
                register_project_name(mh, n_item)

            else:
                n_item.evaluate(mh, node.config)

    # Finally, overwrite options that come from the
    # command-line.
    if not exclusions_only:
        # Common options (from command_line.py) to all tools first:
        if options.octave:
            node.config.octave = True
        if options.ignore_pragmas:
            node.config.pragmas = False

        # Specific options from mh_style:
        if "line_length" in options and options.line_length:
            node.config.style_config["line_length"] = options.line_length
        if "file_length" in options and options.file_length:
            node.config.style_config["file_length"] = options.file_length
        if "tab_width" in options and options.tab_width:
            node.config.style_config["tab_width"] = options.tab_width
        if "copyright_entity" in options and options.copyright_entity:
            node.config.style_config["copyright_entity"] = \
                set(options.copyright_entity)


def apply_exclusions_up(mh, options, dirname):
    assert isinstance(dirname, str)
    assert dirname in tree
    parent_dirname = os.path.dirname(dirname)

    if not tree[dirname].project_root:
        apply_exclusions_up(mh, options, parent_dirname)

    apply_config(mh, options, dirname, exclusions_only=True)


def apply_config_up(mh, options, dirname):
    assert isinstance(dirname, str)
    assert dirname in tree
    parent_dirname = os.path.dirname(dirname)

    if not tree[dirname].project_root:
        apply_config_up(mh, options, parent_dirname)

    apply_config(mh, options, dirname)


def apply_config_down(mh, options, dirname):
    assert isinstance(dirname, str)
    assert dirname in tree

    node = tree[dirname]

    if node.subtree_included:
        # We've already gone down this path
        return

    if DEBUG_TRACE_TREE:
        print("Going down in %s" % dirname)

    for dirent in os.scandir(dirname):
        # Only consider directories
        if not dirent.is_dir(follow_symlinks = False):
            continue

        # Skip hidden directories (e.g. .git)
        if dirent.name.startswith("."):
            continue

        # Skip excluded directories
        if dirent.name in node.excluded_children:
            continue

        child_dirname = os.path.join(dirname, dirent.name)

        register_parent(mh, options, child_dirname)
        apply_config(mh, options, child_dirname)
        apply_config_down(mh, options, child_dirname)


def register_dir(mh, options, dirname, register_subdirs):
    assert isinstance(mh, Message_Handler)
    assert isinstance(dirname, str)
    assert isinstance(register_subdirs, bool)

    if DEBUG_TRACE_TREE:
        print("Registering %s" % dirname)

    # First, we search upwards to find the project root.
    if dirname not in tree:
        register_parent(mh, options, dirname)

    # We then walk up the tree from our project root to apply
    # configuration partially (only exclusions). We do this because
    # there may be dir_exclusions which in turn act as new project
    # roots. For example:
    #
    # src (contains config and is root)
    #   \ foo (excluded)
    #   \ bar
    #
    # If we invoke miss_hit from src with src/foo/wibble.m we should
    # analyze the file as requested with a default configuration
    # (since foo is a project root).
    apply_exclusions_up(mh, options, dirname)

    # We then walk up the tree again from our (possibly different)
    # project root, applying configuration properly this time.
    apply_config_up(mh, options, dirname)

    # Finally, we walk down from our directory (if requested) applying
    # configuration as we go.
    if register_subdirs:
        apply_config_down(mh, options, dirname)


##############################################################################
# Public API
##############################################################################

def get_excluded_directories(dirname):
    assert isinstance(dirname, str)

    if not os.path.exists(dirname):
        raise ICE("%s does not exist" % dirname)

    elif not os.path.isdir(dirname):
        raise ICE("%s is not a directory" % dirname)

    canonical_name = os.path.abspath(dirname)
    if canonical_name not in tree:
        raise ICE("%s was not registered" % dirname)

    return tree[canonical_name].excluded_children


def get_config(filename):
    assert isinstance(filename, str)

    if not os.path.exists(filename):
        raise ICE("%s does not exist" % filename)

    elif not os.path.isfile(filename):
        raise ICE("%s is not a file" % filename)

    dirname = os.path.dirname(os.path.abspath(filename))
    if dirname not in tree:
        raise ICE("%s was not registered" % dirname)

    return tree[dirname].config


def register_item(mh, name, options):
    assert isinstance(mh, Message_Handler)
    assert isinstance(name, str)

    if not os.path.exists(name):
        raise ICE("%s does not exist" % name)

    elif os.path.isfile(name):
        register_dir(mh, options,
                     os.path.dirname(os.path.abspath(name)),
                     False)

    elif os.path.isdir(name):
        register_dir(mh, options,
                     os.path.abspath(name),
                     True)

    else:
        raise ICE("%s is neither a file or directory")


def get_root(name):
    assert isinstance(name, str)

    dirname = os.path.abspath(name)
    if dirname not in tree:
        raise ICE("%s was not registered" % dirname)

    while not tree[dirname].project_root:
        dirname = os.path.dirname(dirname)

    return dirname


def validate_project_config(mh):
    for n_item in project_names.values():
        n_item.validate(mh, project_names)


def get_entry_point(name):
    # Get library or entry-point with the given name
    if name not in project_names:
        return None
    return project_names[name]


def get_global_libraries():
    for n_item in project_names.values():
        if isinstance(n_item, Library_Declaration) and \
           n_item.is_global:
            yield n_item


def get_source_path(n_item):
    assert isinstance(n_item, (Library_Declaration,
                               Entrypoint_Declaration))
    item_list = []
    for n_glib in get_global_libraries():
        item_list += n_glib.get_source_path()
    item_list += n_item.get_source_path()
    return item_list


def get_test_path(n_item):
    assert isinstance(n_item, (Library_Declaration,
                               Entrypoint_Declaration))
    item_list = []
    for n_glib in get_global_libraries():
        item_list += n_glib.get_test_path()
    item_list += n_item.get_test_path()
    return item_list


##############################################################################
# Sanity testing
#############################################################################

def sanity_test():
    # pylint: disable=import-outside-toplevel
    from argparse import ArgumentParser
    import traceback
    # pylint: enable=import-outside-toplevel

    ap = ArgumentParser()
    ap.add_argument("item", metavar="FILE|DIR")
    ap.add_argument("--no-tb",
                    action="store_true",
                    default=False,
                    help="Do not show debug-style backtrace")
    options = ap.parse_args()

    mh = Message_Handler("debug")
    mh.sort_messages = False
    mh.colour = False

    try:
        register_item(mh, options.item, options)

    except Error:
        if not options.no_tb:
            traceback.print_exc()

    except ICE as ice:
        if not options.no_tb:
            traceback.print_exc()
        print("ICE:", ice.reason)

    for dirname in sorted(tree):
        print("Showing config for %s" % dirname)

        node = tree[dirname]
        print("  Root: %s" % node.project_root)
        print("  File: %s" % ", ".join(node.config_files))

        cfg = node.config
        if cfg is None:
            print("  No config attached")
            continue

        print("  Enabled = %s" % cfg.enabled)
        print("  Octave  = %s" % cfg.octave)
        print("  Rules   = %u" % len(cfg.style_rules))
        print("  SConf   = %s" % cfg.style_config)
        print("  Metrics = %u" % len(cfg.enabled_metrics))
        print("  Limits  = %s" % cfg.metric_limits)


if __name__ == "__main__":
    sanity_test()
