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

# This is a small helper tool that, when given a directory, will
# display all Simulink block types in all slx models in that
# directory.

import os
import argparse

import command_line
from s_parser import *

# pylint: disable=invalid-name
all_block_kinds = set()


def process(mh, root_dir, file_name):
    # pylint: disable=global-statement
    # pylint: disable=unused-argument
    global all_block_kinds
    # short_name = file_name[len(root_dir.rstrip("/")) + 1:]

    mh.register_file(file_name)

    smdl = SIMULINK_Model(mh, file_name, note_harness=False)
    all_block_kinds |= smdl.block_kinds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root_dir")

    options = ap.parse_args()

    mh = Message_Handler("debug")
    mh.sort_messages = False

    for path, _, files in os.walk(options.root_dir):
        for f in files:
            if f.endswith(".slx"):
                process(mh, options.root_dir, os.path.join(path, f))

    print("Sorted list of all Simulink blocks types (%u) present:" %
          len(all_block_kinds))
    for block_type in sorted(all_block_kinds):
        print("   %s" % block_type)

    mh.summary_and_exit()


if __name__ == "__main__":
    command_line.ice_handler(main)
