#!/usr/bin/env python

import os

import util.changelog

from miss_hit_core.version import VERSION_TUPLE

major, minor, release = VERSION_TUPLE
release += 1

# Bump version and update version.py

tmp = ""
with open("miss_hit_core/version.py", "r") as fd:
    for raw_line in fd:
        if raw_line.startswith("VERSION_TUPLE"):
            raw_line = 'VERSION_TUPLE = (%u, %u, %u)\n' % (major,
                                                           minor,
                                                           release)
        elif raw_line.startswith("VERSION_SUFFIX"):
            raw_line = 'VERSION_SUFFIX = "dev"\n'

        tmp += raw_line
with open("miss_hit_core/version.py", "w") as fd:
    fd.write(tmp)

VERSION = "%u.%u.%u-dev" % (major, minor, release)

# Update changelog and docs, adding a new entry

util.changelog.add_new_section(VERSION)
os.system("make doc")

# Assemble commit

os.system("git add miss_hit_core/version.py CHANGELOG.md docs")
os.system('git commit -m "Bump version to %s after release"' % VERSION)
