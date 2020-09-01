#!/usr/bin/env python3

import json
import os
import argparse
from pprint import pprint

def build_dot(name, symbol):
    pprint(symbol)

def strip_comments(js):
    required_comments = frozenset(["#identifier"])
    if isinstance(js, dict):
        comments = [x
                    for x in js
                    if x.startswith("#") and not x in required_comments]
        for k in comments:
            del js[k]
        for k in js:
            strip_comments(js[k])
    elif isinstance(js, list):
        for v in js:
            strip_comments(v)

def process(filename):
    with open(filename, "r") as fd:
        stab = json.load(fd)["symbolTable"]

    sst = {}
    print ("top-level symbols:")
    for name in sorted(stab):
        print("   %s" % name)

        if not name.startswith("__CPROVER") and name != "return'":
            strip_comments(stab[name])
            build_dot(name, stab[name])
            sst[name] = stab[name]
        elif name == "__CPROVER_initialize":
            strip_comments(stab[name])
            build_dot(name, stab[name])
            sst[name] = stab[name]

    with open("stripped.json_symtab", "w") as fd:
        json.dump({"symbolTable" : sst}, fd, indent=4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("filename")

    options = ap.parse_args()

    if not os.path.isfile(options.filename):
        ap.error("not a file")

    process(options.filename)


if __name__ == "__main__":
    main()
