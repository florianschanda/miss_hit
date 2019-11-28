#!/usr/bin/env python3

import os
import subprocess

TEST_ROOT = os.getcwd()


def execute_style_test(name):
    print("Running style test %s" % name)

    os.chdir(os.path.join(TEST_ROOT,
                          "style",
                          name))

    m_files = []
    for path, _, files in os.walk("."):
        for f in files:
            if f.endswith(".m"):
                m_files.append(os.path.join(path, f))

    # Take a copy of the original file
    orig = {}
    for f in m_files:
        with open(f, "r") as fd:
            orig[f] = fd.read()

    r = subprocess.run(["../../../mh_style.py",
                        ".",
                        "--fix"],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       encoding="utf-8")

    # Rename the fixed files, and restore the original
    for f in m_files:
        os.rename(f, f + "_fixed")
        with open(f, "w") as fd:
            fd.write(orig[f])

    # Save stdout
    with open("expected_out.txt", "w") as fd:
        fd.write(r.stdout)


def main():
    # Make sure we're in the right directory
    assert os.path.isfile("../mh_style.py")

    for t in os.listdir("style"):
        execute_style_test(t)


if __name__ == "__main__":
    main()
