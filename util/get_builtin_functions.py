#!/usr/bin/env python

import argparse
import os
import re
import sys

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))
from m_language import KEYWORDS

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("matlab_root")
    options = ap.parse_args()

    if not os.path.isdir(options.matlab_root):
        ap.error("%s is not a directory" % options.matlab_root)

    if not os.path.isfile(os.path.join(options.matlab_root,
                                       "bin",
                                       "matlab")):
        ap.error("%s does not look like a matlab install" % options.matlab_root)

    version = None
    with open(os.path.join(options.matlab_root,
                           "VersionInfo.xml"),
              "r") as fd:
        for raw_line in fd:
            rel = re.search("<release>([a-zA-Z0-9]+)</release>", raw_line)
            if rel:
                version = rel.group(1)
    assert version is not None

    toolbox = os.path.join(options.matlab_root, "toolbox", "matlab")

    functions = set()

    for path, dirs, files in os.walk(toolbox):
        dirs.sort()
        for f in files:
            if f.endswith(".m"):
                with open(os.path.join(path, f), "r") as fd:
                    tmp = fd.read()
                if re.search("[Bb]uilt-?in function", tmp):
                    name = f[:-2]
                    functions.add(name)

    functions -= KEYWORDS

    with open(os.path.join("..", "m_language_builtins.py"), "w") as fd:
        fd.write("# This file is auto-generated with util/get_builtin_functions\n")
        fd.write("# for MATLAB release %s\n\n" % version)
        fd.write("BUILTIN_FUNCTIONS = frozenset([\n")
        for fn in sorted(functions):
            fd.write("    \"%s\",\n" % fn)
        fd.write("])\n")


if __name__ == "__main__":
    main()
