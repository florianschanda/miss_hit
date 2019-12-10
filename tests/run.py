#!/usr/bin/env python3

import os
import sys
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

    # Run in plaintext mode
    r = subprocess.run(["../../../mh_style.py",
                        ".",
                        "--fix"],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       encoding="utf-8")
    plain_out = r.stdout

    # Rename the fixed files, and restore the original
    for f in m_files:
        os.rename(f, f + "_fixed")
        with open(f, "w") as fd:
            fd.write(orig[f])

    # Run in HTML mode
    r = subprocess.run(["../../../mh_style.py",
                        ".",
                        "--html=expected_out.html"],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       encoding="utf-8")
    html_out = r.stdout

    # Save stdout
    with open("expected_out.txt", "w") as fd:
        fd.write("=== PLAIN MODE ===\n")
        fd.write(plain_out)
        fd.write("\n")
        fd.write("=== HTML MODE ===\n")
        fd.write(html_out)

def execute_parser_test(name):
    print("Running parser test %s" % name)

    os.chdir(os.path.join(TEST_ROOT,
                          "parser",
                          name))

    files = [f
             for f in os.listdir(".")
             if f.endswith(".m")]

    for f in files:
        r = subprocess.run([sys.executable,
                            "../../../m_parser.py",
                            "--no-tb",
                            f],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           encoding="utf-8")
        plain_out = r.stdout

        with open(f + ".out", "w") as fd:
            fd.write(plain_out)


def main():
    # Make sure we're in the right directory
    assert os.path.isfile("../mh_style.py")
    root = os.getcwd()

    os.chdir(root)
    for t in os.listdir("style"):
        execute_style_test(t)

    os.chdir(root)
    for t in os.listdir("parser"):
        execute_parser_test(t)


if __name__ == "__main__":
    main()
