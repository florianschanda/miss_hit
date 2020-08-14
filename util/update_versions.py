#!/usr/bin/env python3

import os
import sys
import re
import html
sys.path.append("..")

from miss_hit_core import version

def process(filename):
    tmp = []
    with open(filename, "r") as fd:
        for raw_line in fd:
            if raw_line.strip().startswith("<header>MISS_HIT"):
                tmp.append(re.sub("MISS_HIT( "
                                  "[0-9]+\.[0-9]+\.[0-9]+"
                                  "(-[a-z0-9]+)?)?",
                                  version.FULL_NAME,
                                  raw_line))
            else:
                tmp.append(raw_line)

    with open(filename, "w") as fd:
        fd.write("".join(tmp))


for path, _, files in os.walk("../docs"):
    for f in files:
        if f.endswith(".html"):
            process(os.path.join(path, f))
