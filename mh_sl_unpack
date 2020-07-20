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

# This tool unpacks new-style simulink models so they can be more
# easily inspected.

import argparse
import os.path
import shutil
import sys
import zipfile


def process(filename):
    core_name = filename.replace(".slx", "_unpacked")
    if os.path.isfile(core_name):
        print("cannot unpack %s, unpacked name exists and is a file" %
              filename)
        sys.exit(1)
    elif os.path.isdir(core_name):
        shutil.rmtree(core_name)

    with zipfile.ZipFile(filename, "r") as zf:
        for name in zf.namelist():
            dst_name = os.path.join(core_name, name)
            os.makedirs(os.path.dirname(dst_name), exist_ok=True)
            with zf.open(name) as in_fd:
                with open(dst_name, "wb") as out_fd:
                    out_fd.write(in_fd.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", metavar="FILE|DIR")

    options = ap.parse_args()

    if os.path.isfile(options.name):
        if options.name.endswith(".slx"):
            process(options.name)
        else:
            ap.error("must be a .slx file")
    elif os.path.isdir(options.name):
        for path, _, files in os.walk(options.name):
            for f in files:
                if f.endswith(".slx"):
                    process(os.path.join(path, f))
    else:
        ap.error("cannot find file or directory")


if __name__ == "__main__":
    main()
