#!/usr/bin/env python

import argparse
import os
import re
import sys

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))
from m_language import KEYWORDS

high_impact_builtins = set([
    "cd",
    "clock",
    "close",
    "cputime",
    "eps",
    "eye",
    "false",
    "flintmax",
    "horzcat",
    "inf",
    "Inf",
    "isdeployed",
    "lasterr",
    "lastwarn",
    "license",
    "more",
    "nan",
    "NaN",
    "nargin",
    "nargout",
    "newline",
    "ones",
    "pi",
    "rand",
    "randn",
    "realmax",
    "realmin",
    "speye",
    "tic",
    "toc",
    "true",
    "vertcat",
    "zeros",
    "single",
    "double",
    "int8",
    "int16",
    "int32",
    "int64",
    "uint8",
    "uint16",
    "uint32",
    "uint64",
    "clear",
    "exit",
    "quit",
    "close"
])
# This is a list of hand-picked built-ins are definitely not a good
# idea to overwrite.

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

    builtin_functions = set(["NaN", "Inf"])
    # There capitalised versions of nan and inf.
    extra_functions = set()
    namespaces = set()
    builtin_classes = set()
    special_vars = set(["Contents"])

    for path, dirs, files in os.walk(toolbox):
        dirs.sort()

        # Exclude packages (they are already in a different namespace)
        for i in reversed(range(len(dirs))):
            if dirs[i].startswith("+"):
                namespaces.add(dirs[i][1:])
                del dirs[i]
            elif dirs[i].startswith("@"):
                builtin_classes.add(dirs[i][1:])
                del dirs[i]
            elif dirs[i] in ("demos", "private"):
                # Remove examples or private directories
                del dirs[i]

        for f in files:
            if f.endswith(".m") and f not in ("Contents.m", "debug.m"):
                with open(os.path.join(path, f), "r") as fd:
                    tmp = fd.read()
                name = f[:-2]
                if re.search("[Bb]uilt-?in function", tmp):
                    builtin_functions.add(name)
                else:
                    classified = False
                    for line in tmp.splitlines():
                        if line.strip().startswith("function"):
                            extra_functions.add(name)
                            classified = True
                            break
                        elif line.strip().startswith("classdef"):
                            builtin_classes.add(name)
                            classified = True
                            break
                    if not classified:
                        # We assume it's just a builtin function at this point
                        builtin_functions.add(name)

    # Some of the basic statements have help text associated. We
    # remove them at this point.
    builtin_functions -= KEYWORDS

    # For some reason the classdef construct is not documented as a
    # built-in. We remove that one specifically here, and otherwise
    # assert that a non-builtin function will have code attached.
    extra_functions -= set(["classdef"])
    assert len(extra_functions & KEYWORDS) == 0

    assert len(high_impact_builtins - builtin_functions) == 0, \
        ", ".join(high_impact_builtins - builtin_functions)

    with open(os.path.join("..", "m_language_builtins.py"), "w") as fd:
        fd.write("# This file is auto-generated with util/get_builtin_functions\n")
        fd.write("# for MATLAB release %s\n\n" % version)

        fd.write("HIGH_IMPACT_BUILTIN_FUNCTIONS = frozenset([\n")
        for fn in sorted(high_impact_builtins):
            fd.write("    \"%s\",\n" % fn)
        fd.write("])\n\n")

        fd.write("BUILTIN_FUNCTIONS = frozenset([\n")
        for fn in sorted(builtin_functions):
            fd.write("    \"%s\",\n" % fn)
        fd.write("])\n\n")

        fd.write("EXTRA_FUNCTIONS = frozenset([\n")
        for fn in sorted(extra_functions):
            fd.write("    \"%s\",\n" % fn)
        fd.write("])\n\n")

        fd.write("BUILTIN_CLASSES = frozenset([\n")
        for fn in sorted(builtin_classes):
            fd.write("    \"%s\",\n" % fn)
        fd.write("])\n\n")

        fd.write("BUILTIN_NAMESPACES = frozenset([\n")
        for fn in sorted(namespaces):
            fd.write("    \"%s\",\n" % fn)
        fd.write("])\n\n")

        fd.write("SPECIAL_NAMES = frozenset([\n")
        for fn in sorted(special_vars):
            fd.write("    \"%s\",\n" % fn)
        fd.write("])\n")

if __name__ == "__main__":
    main()
