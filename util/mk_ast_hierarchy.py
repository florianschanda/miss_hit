#!/usr/bin/env python3

"""
This little hack draws a hierarchy of the AST nodes in GraphViz format.
"""

import inspect
import argparse

import miss_hit_core.m_ast
import miss_hit_core.s_ast
import miss_hit_core.cfg_ast


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("component", metavar="s|m|cfg")
    options = ap.parse_args()

    if options.component == "s":
        module = miss_hit.s_ast
    elif options.component == "m":
        module = miss_hit.m_ast
    elif options.component == "cfg":
        module = miss_hit.cfg_ast
    else:
        ap.error("component must be either s(imulink), m(atlab), or cfg")

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
