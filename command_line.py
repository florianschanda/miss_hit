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

# This is the common command-line handling for all MISS_HIT tools.

import os
import sys
import argparse
import traceback
import textwrap

import config_files
import errors


GITHUB_ISSUES = "https://github.com/florianschanda/miss_hit/issues"


def create_basic_clp():
    rv = {}

    ap = argparse.ArgumentParser(
        description="MATLAB Independent, Small & Safe, High Integrity Tools")
    rv["ap"] = ap

    ap.add_argument("files",
                    metavar="FILE|DIR",
                    nargs="*",
                    help="MATLAB files or directories to analyze")
    ap.add_argument("--ignore-config",
                    action="store_true",
                    default=False,
                    help=("Ignore all %s files." %
                          " or ".join(config_files.CONFIG_FILENAMES)))

    output_options = ap.add_argument_group("output options")
    rv["output_options"] = output_options

    output_options.add_argument("--brief",
                                action="store_true",
                                default=False,
                                help="Don't show line-context on messages")

    language_options = ap.add_argument_group("language options")
    rv["language_options"] = language_options

    language_options.add_argument("--octave",
                                  default=False,
                                  action="store_true",
                                  help=("Enable support for the Octave"
                                        " language. Note: This is highly"
                                        " incomplete right now, only the"
                                        " # comments are supported."))

    debug_options = ap.add_argument_group("debugging options")
    rv["debug_options"] = debug_options

    return rv


def parse_args(clp):
    options = clp["ap"].parse_args()

    if not options.brief and sys.stdout.encoding != "UTF-8":
        print("WARNING: It looks like your environment is not set up quite")
        print("         right since python will encode to %s on stdout." %
              sys.stdout.encoding)
        print()
        print("To fix set one of the following environment variables:")
        print("   LC_ALL=en_GB.UTF-8 (or something similar)")
        print("   PYTHONIOENCODING=UTF-8")

    if not options.files:
        clp["ap"].error("at least one file or directory is required")

    for item in options.files:
        if not (os.path.isdir(item) or os.path.isfile(item)):
            clp["ap"].error("%s is neither a file nor directory" % item)

    return options


def read_config(mh, options):
    try:
        for item in options.files:
            if os.path.isdir(item):
                config_files.register_tree(mh,
                                           os.path.abspath(item),
                                           options)

            elif os.path.isfile(item):
                config_files.register_tree(
                    mh,
                    os.path.dirname(os.path.abspath(item)),
                    options)

        config_files.build_config_tree(mh,
                                       options)

    except errors.Error:
        mh.summary_and_exit()


def ice_handler(main_function):
    try:
        main_function()
    except errors.ICE as internal_compiler_error:
        traceback.print_exc()
        print("-" * 70)
        print("- Encountered an internal compiler error. This is a tool")
        print("- bug, please report it on our github issues so we can fix it:")
        print("-")
        print("-    %s" % GITHUB_ISSUES)
        print("-")
        print("- Please include the above backtrace in your bug report, and")
        print("- the following information:")
        print("-")
        lines = textwrap.wrap(internal_compiler_error.reason)
        print("\n".join("- %s" % l for l in lines))
        print("-" * 70)
