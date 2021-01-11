#!/usr/bin/env python3

import sys
import os
import subprocess
import datetime


def get_changed_files():
    proc = subprocess.run(["git", "diff",
                           "--name-only",
                           "origin/master",
                           "HEAD"],
                          stdout=subprocess.PIPE,
                          encoding="UTF-8")
    return proc.stdout.splitlines()


def check(filename, current_year):
    assert os.path.isfile(filename)
    assert isinstance(current_year, int)

    # Ignore files not in the core source directories
    if not filename.startswith("miss_hit"):
        return None

    with open(filename, "r") as fd:
        for raw_line in fd:
            if raw_line.startswith("#"):
                content = raw_line.strip().strip("#").strip()
                if content.startswith("Copyright (C)"):
                    years = content.split()
                    if len(years) < 3:
                        return "malformed copyright entry"
                    years = years[2].rstrip(",")
                    if "-" in years:
                        year = years.split("-", 1)[1]
                    else:
                        year = years
                    try:
                        year = int(year)
                    except ValueError:
                        return "malformed year '%s'" % years
                    if year >= current_year:
                        return None
            else:
                break

    return "copyright does not cover %u" % current_year


def main():
    current_year = datetime.datetime.now().year

    problems = False
    for filename in get_changed_files():
        if os.path.exists(filename):
            error = check(filename, current_year)
            if error:
                print("%s: %s" % (filename, error))
                problems = True

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
