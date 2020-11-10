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

# This is a small helper tool to diff code inside simulink models. It
# is designed to be used with git difftool.

import os
import argparse
import difflib
import tempfile

from miss_hit_core.config import Config
from miss_hit_core.errors import Message_Handler
from miss_hit_core.s_parser import Simulink_SLX_Parser
from miss_hit_core import s_ast


def load_file(mh, filename):
    mh.register_file(filename)
    slp = Simulink_SLX_Parser(mh, filename, Config())
    n_container = slp.parse_file()
    return n_container


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file_before")
    ap.add_argument("file_after")

    ap.add_argument("--kdiff3",
                    help="Use KDiff3 to show a visual diff",
                    action="store_true",
                    default=False)

    ap.add_argument("--allow-weird-names",
                    help=("Permit file names not ending in .slx (use at "
                          "your own risk)"),
                    action="store_true",
                    default=False)

    options = ap.parse_args()

    for item in (options.file_before, options.file_after):
        if not os.path.isfile(item):
            ap.error("%s is not a file" % item)
        elif not item.endswith(".slx") and not options.allow_weird_names:
            ap.error("%s is not a modern (slx) Simulink model")

    mh = Message_Handler("diff")

    n_before = load_file(mh, options.file_before)
    n_after  = load_file(mh, options.file_after)

    code_blocks = {}

    for side in ("before", "after"):
        n_root = n_before if side == "before" else n_after
        for n_block in n_root.iter_all_blocks():
            if not isinstance(n_block, s_ast.Matlab_Function):
                continue
            name = n_block.local_name()
            if name not in code_blocks:
                code_blocks[name] = {"before" : None,
                                     "after"  : None}
            code_blocks[name][side] = n_block.get_text()

    first = True

    for name in sorted(code_blocks):
        before = code_blocks[name]["before"]
        after  = code_blocks[name]["after"]

        if before == after:
            continue

        if first:
            first = False
        else:
            print()

        print("Difference in MATLAB Code block '%s'" % name)
        if before is None:
            if options.kdiff3:
                with tempfile.TemporaryDirectory() as dirname:
                    with open(os.path.join(dirname, "before"), "w") as fd:
                        pass
                    with open(os.path.join(dirname, "after"), "w") as fd:
                        fd.write(after)
                    cmd = "kdiff3 %s %s" % (os.path.join(dirname, "before"),
                                            os.path.join(dirname, "after"))
                    os.system(cmd)
            else:
                print("NEW block containing:")
                print("=" * 78)
                print(before)
                print("=" * 78)
        elif after is None:
            print("DELETED block")
        else:
            if options.kdiff3:
                with tempfile.TemporaryDirectory() as dirname:
                    with open(os.path.join(dirname, "before"), "w") as fd:
                        fd.write(before)
                    with open(os.path.join(dirname, "after"), "w") as fd:
                        fd.write(after)
                    cmd = "kdiff3 %s %s" % (os.path.join(dirname, "before"),
                                            os.path.join(dirname, "after"))
                    os.system(cmd)
            else:
                print("CHANGED block:")
                print("=" * 78)
                print("\n".join(
                    difflib.unified_diff(before.splitlines(),
                                         after.splitlines(),
                                         fromfile=options.file_before,
                                         tofile=options.file_after)))
                print("=" * 78)

    return 0


if __name__ == "__main__":
    main()
