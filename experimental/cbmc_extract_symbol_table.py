#!/usr/bin/env python3

import subprocess
import os
import argparse
import json

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("filename")

    options = ap.parse_args()

    if not os.path.isfile(options.filename):
        ap.error("not a file")

    result = subprocess.run(["cbmc",
                             options.filename,
                             "--json-ui",
                             #"--no-arch",
                             #"--no-library",
                             "--show-symbol-table"],
                            capture_output=True)

    output = json.loads(result.stdout)
    st = None
    for item in output:
        if "symbolTable" in item:
            st = item
    assert st is not None

    outfile = options.filename.replace(".c", ".json_symtab")

    with open(outfile, "w") as fd:
        print("Written GOTO symbol table to %s" % outfile)
        json.dump(st, fd, indent=2)

if __name__ == "__main__":
    main()
