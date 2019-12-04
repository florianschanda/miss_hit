#!/usr/bin/env python3

import os
import re
import argparse

def process(fn):
    test_id = 0
    with open(fn, "r") as fd:
        tmp = fd.read().split("\n\n")
    for item in tmp:
        if "%!" not in item:
            continue
        test_id += 1
        test_fn = False
        tf = ["% This test is extracted from the GNU Octave testsuite",
              "%% For a full copyright please refert to %s from GNU Octave" %
              os.path.basename(fn),
              ""]
        for line in item.splitlines():
            if line.startswith("%!"):
                line = line[2:]
            line = line.replace("endfunction", "end")
            assert_m = re.match("^assert ?\((.+), ?(.+)\);$", line.strip())
            if line.strip() == "test":
                test_fn = True
                tf.append("")
                tf.append("function test()")
            elif line.startswith("#"):
                tf.append("% " + line.lstrip("#").strip())
            elif assert_m:
                indent = len(line) - len(line.lstrip())
                tf.append((" " * indent) +
                          "assert (%s == %s);" % (assert_m.group(1),
                                                  assert_m.group(2)))
            else:
                tf.append(line.rstrip())
        if test_fn:
            tf.append("end")
            # tf.insert(3, "test();")
            # tf.insert(4, "")

        with open("test_%02u.m" % test_id, "w") as fd:
            fd.write("\n".join(tf) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")

    options = ap.parse_args()

    process(options.file)


if __name__ == "__main__":
    main()
