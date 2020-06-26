#!/usr/bin/env python3

import os
import sys
import copy
import subprocess
import multiprocessing
import argparse

TEST_ROOT = os.getcwd()
TEST_ENV = copy.copy(os.environ)
TEST_ENV["PYTHONIOENCODING"] = "UTF-8"

def execute_style_test(name):
    os.chdir(os.path.join(TEST_ROOT,
                          "style",
                          name))

    m_files = []
    slx_files = []
    for path, _, files in os.walk("."):
        for f in files:
            if f.endswith(".m"):
                m_files.append(os.path.join(path, f))
            elif f.endswith(".slx"):
                slx_files.append(os.path.join(path, f))

    # Take a copy of the original file
    orig = {}
    fixed = {}
    for f in m_files + slx_files:
        with open(f, "rb") as fd:
            orig[f] = fd.read()

    # Run in HTML mode
    r = subprocess.run([sys.executable,
                        "../../../mh_style.py",
                        ".",
                        "--single",
                        "--process-slx",
                        "--html=expected_out.html"],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       encoding="utf-8",
                       env=TEST_ENV)
    html_out = r.stdout

    # Run in plaintext mode and fix
    r = subprocess.run([sys.executable,
                        "../../../mh_style.py",
                        "--debug-validate-links",
                        "--debug-cfg",
                        ".",
                        "--single",
                        "--process-slx",
                        "--fix"],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       encoding="utf-8",
                       env=TEST_ENV)
    plain_out = r.stdout

    # Write the fixed file to foo.m_fixed
    for f in m_files + slx_files:
        with open(f, "rb") as fd:
            fixed[f] = fd.read()
        with open(f + "_fixed", "wb") as fd:
            fd.write(fixed[f])

    # Run in plaintext mode, again, to see if more things need fixing
    r = subprocess.run([sys.executable,
                        "../../../mh_style.py",
                        ".",
                        "--single",
                        "--process-slx",
                        "--fix"],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       encoding="utf-8",
                       env=TEST_ENV)
    plain_out_again = r.stdout

    # Check if fixed files not "fixed" again
    broken_fixes = set()
    for f in m_files + slx_files:
        with open(f, "rb") as fd:
            tmp = fd.read()
        if tmp != fixed[f]:
            broken_fixes.add(f)

    # Restore original output
    for f in m_files + slx_files:
        with open(f, "wb") as fd:
            fd.write(orig[f])

    # Save stdout
    with open("expected_out.txt", "w") as fd:
        fd.write("=== PLAIN MODE ===\n")
        fd.write(plain_out)
        fd.write("\n")
        fd.write("=== HTML MODE ===\n")
        fd.write(html_out)
        if broken_fixes:
            fd.write("\n")
            fd.write("=== ! BROKEN FIXES ! ===\n")
            for fail in sorted(broken_fixes):
                fd.write("Fixing is not idempotent for %s\n" % fail)


    return "Ran style test %s" % name


def execute_metric_test(name):
    os.chdir(os.path.join(TEST_ROOT,
                          "metrics",
                          name))

    # Run
    r = subprocess.run([sys.executable,
                        "../../../mh_metric.py",
                        "--single",
                        ".",],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       encoding="utf-8",
                       env=TEST_ENV)
    plain_out = r.stdout

    # HTML
    r = subprocess.run([sys.executable,
                        "../../../mh_metric.py",
                        "--single",
                        "--html=metrics.html",
                        ".",],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,
                       encoding="utf-8",
                       env=TEST_ENV)
    html_out = r.stdout

    # Save stdout
    with open("expected_out.txt", "w") as fd:
        fd.write("=== PLAIN MODE ===\n")
        fd.write(plain_out)

        fd.write("\n\n=== HTML MODE ===\n")
        fd.write(html_out)

    return "Ran metrics test %s" % name


def execute_lexer_test(name):
    os.chdir(os.path.join(TEST_ROOT,
                          "lexer",
                          name))

    files = [f
             for f in os.listdir(".")
             if f.endswith(".m")]

    for f in files:
        r = subprocess.run([sys.executable,
                            "../../../m_lexer.py",
                            f],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           encoding="utf-8",
                           env=TEST_ENV)
        plain_out = r.stdout

        with open(f + ".out", "w") as fd:
            fd.write(plain_out)

    return "Ran lexer test %s" % name


def execute_parser_test(name):
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
                            "--tree",
                            f],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           encoding="utf-8",
                           env=TEST_ENV)
        plain_out = r.stdout

        with open(f + ".out", "w") as fd:
            fd.write(plain_out)

    return "Ran parser test %s" % name


def execute_simulink_parser_test(name):
    os.chdir(os.path.join(TEST_ROOT,
                          "simulink_parser",
                          name))

    files = [f
             for f in os.listdir(".")
             if f.endswith(".slx")]

    for f in files:
        r = subprocess.run([sys.executable,
                            "../../../s_parser.py",
                            f],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           encoding="utf-8",
                           env=TEST_ENV)
        plain_out = r.stdout

        with open(f + ".out", "w") as fd:
            fd.write(plain_out)

    return "Ran simulink parser test %s" % name


def run_test(test):
    if os.path.exists(os.path.join(TEST_ROOT,
                                   test["kind"],
                                   test["test"],
                                   "ONLY_LINUX")):
        if sys.platform != "linux":
            return "SKIPPED linux-only test %s" % test["test"]

    fn = {
        "style"           : execute_style_test,
        "metrics"         : execute_metric_test,
        "lexer"           : execute_lexer_test,
        "parser"          : execute_parser_test,
        "simulink_parser" : execute_simulink_parser_test,
    }
    return fn[test["kind"]](test["test"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--single",
                    action="store_true",
                    default=False)
    ap.add_argument("--suite",
                    default=None)

    options = ap.parse_args()

    # Make sure we're in the right directory
    assert os.path.isfile("../mh_style.py")
    root = os.getcwd()

    tests = []

    if options.suite:
        suites = [options.suite]
    else:
        suites = ["lexer", "parser", "simulink_parser", "style", "metrics"]

    for kind in suites:
        for t in os.listdir(kind):
            tests.append({"kind" : kind,
                          "test" : t})

    if options.single:
        for t in tests:
            print("Running %s" % t)
            print(run_test(t))
    else:
        pool = multiprocessing.Pool()
        for res in pool.imap_unordered(run_test, tests, 2):
            print(res)


if __name__ == "__main__":
    main()
