#!/usr/bin/env python3

# Helper script to remove "-dev" from current version; update
# changelog/docs; and commit.

import os

import util.changelog

# Update version.py to remove the -dev (or if given) use a different
# version number.

tmp = ""
with open("miss_hit/version.py", "r") as fd:
    for raw_line in fd:
        if raw_line.startswith("VERSION_SUFFIX"):
            raw_line = 'VERSION_SUFFIX = ""\n'

        tmp += raw_line
with open("miss_hit/version.py", "w") as fd:
    fd.write(tmp)

from miss_hit.version import VERSION
print(VERSION)

# Update last CHANGELOG entry and documentation to use the new
# version.

util.changelog.set_current_title(VERSION)
os.system("make doc")

# Commit & tag

os.system("git add CHANGELOG.md docs miss_hit/version.py")
os.system('git commit -m "Release %s"' % VERSION)
