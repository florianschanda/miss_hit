#!/usr/bin/env python3

"""
This little hack draws a hierarchy of the AST nodes in GraphViz format.
"""

import sys
sys.path.append(".")

import inspect
import m_ast


def main():
    print("digraph {")
    print('rankdir="LR";')
    for name, c in inspect.getmembers(m_ast, inspect.isclass):
        if not issubclass(c, m_ast.Node):
            continue
        print('"%s";' % name)
        for b in c.__bases__:
            if issubclass(b, m_ast.Node):
                print('"%s" -> "%s";' % (b.__name__, name))
    print("}")


if __name__ == "__main__":
    main()
