#!/usr/bin/env python3

"""
This little hack draws a hierarchy of the AST nodes in GraphViz format.
"""

import sys
sys.path.append(".")

import inspect
import m_ast
import s_ast
import argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("component", metavar="s|m")
    options = ap.parse_args()

    if options.component not in ("s", "m"):
        ap.error("component must be either s or m")
    elif options.component == "m":
        module = m_ast
    else:
        module = s_ast

    print("digraph {")
    print('rankdir="LR";')
    for name, c in inspect.getmembers(module, inspect.isclass):
        if not issubclass(c, module.Node):
            continue
        print('"%s";' % name)
        for b in c.__bases__:
            if issubclass(b, module.Node):
                print('"%s" -> "%s";' % (b.__name__, name))
    print("}")


if __name__ == "__main__":
    main()
