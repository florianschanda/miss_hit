#!/usr/bin/env python3

import os

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

# Update last CHANGELOG entry to use the new version. We also extract
# the items in the last entry to be used in our commmit message.

tmp = ""
relevant_log = ""
mode = "searching for changelog"
with open("CHANGELOG.md", "r") as fd:
    for raw_line in fd:
        if mode == "searching for changelog":
            if raw_line.startswith("## Changelog"):
                mode = "searching for first entry"
        elif mode == "searching for first entry":
            if raw_line.startswith("### "):
                raw_line = "### %s\n" % VERSION
                mode = "eating log"
        elif mode == "eating log":
            if raw_line.startswith("### "):
                mode = "done"
            else:
                relevant_log += raw_line
        else:
            pass
        tmp += raw_line
with open("CHANGELOG.md", "w") as fd:
    fd.write(tmp)

# Run documentation update

os.system("make doc")

# Write commit message to file

with open("commit_msg", "w") as fd:
    fd.write("release-%s\n\n" % VERSION)
    fd.write(relevant_log.strip())
    fd.write("\n")

# Commit & tag

os.system("git add CHANGELOG.md docs miss_hit/version.py")
os.system("git commit -F commit_msg")
os.system("git tag release-%s" % VERSION)

# Clean up

os.unlink("commit_msg")
