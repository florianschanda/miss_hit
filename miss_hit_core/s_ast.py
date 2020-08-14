#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2020, Florian Schanda                         ##
##                                                                          ##
##  This file is part of MISS_HIT.                                          ##
##                                                                          ##
##  MATLAB Independent, Small & Safe, High Integrity Tools (MISS_HIT) is    ##
##  free software: you can redistribute it and/or modify it under the       ##
##  terms of the GNU General Public License as published by the Free        ##
##  Software Foundation, either version 3 of the License, or (at your       ##
##  option) any later version.                                              ##
##                                                                          ##
##  MISS_HIT is distributed in the hope that it will be useful,             ##
##  but WITHOUT ANY WARRANTY; without even the implied warranty of          ##
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           ##
##  GNU General Public License for more details.                            ##
##                                                                          ##
##  You should have received a copy of the GNU General Public License       ##
##  along with MISS_HIT. If not, see <http://www.gnu.org/licenses/>.        ##
##                                                                          ##
##############################################################################

# This is a class structure to represent an AST in the Simulink
# language.

from abc import ABCMeta, abstractmethod
import xml.etree.ElementTree as ET

import os.path

from miss_hit_core.errors import Location


class Source_Reference(metaclass=ABCMeta):
    # A reference back to the original model. Can be either to a
    # new-style XML model or a legacy plain-text model.

    @abstractmethod
    def get_text(self):
        pass

    @abstractmethod
    def set_text(self, text):
        pass


class SLX_Reference(Source_Reference):
    def __init__(self, et_node):
        assert isinstance(et_node, ET.Element)
        self.et_node = et_node

    def get_text(self):
        return self.et_node.text

    def set_text(self, text):
        assert isinstance(text, str)
        self.et_node.text = text


class Node(metaclass=ABCMeta):
    def __init__(self):
        self.n_parent = None

    def set_parent(self, n_parent):
        assert isinstance(n_parent, Node)
        self.n_parent = n_parent

    @abstractmethod
    def dump_hierarchy(self, indent):
        pass


class Container(Node):
    # pylint: disable=abstract-method

    def __init__(self, filename):
        super().__init__()
        assert isinstance(filename, str)

        self.filename = filename
        # Filename.

        self.name = os.path.splitext(os.path.basename(filename))[0]
        # Name of the model (derived from filename).

        self.n_system = None
        # Pointer to the system.

        self.encoding = "utf-8"
        # The character encoding used for things inside this
        # container. We default to utf-8.

    def set_system(self, n_system):
        assert isinstance(n_system, System)
        self.n_system = n_system
        self.n_system.set_parent(self)

    def set_encoding(self, encoding):
        assert isinstance(encoding, str)
        self.encoding = encoding

    def loc(self):
        return Location(self.filename)

    def iter_all_blocks(self):
        yield from self.n_system.iter_all_blocks()


class Model(Container):
    def dump_hierarchy(self, indent=0):
        print(" " * indent, "Model")
        self.n_system.dump_hierarchy(indent + 1)


class Library(Container):
    def dump_hierarchy(self, indent=0):
        print(" " * indent, "Library")
        self.n_system.dump_hierarchy(indent + 1)


class System(Node):
    # This is a system (in Simulink this is all you can see on each
    # screen).
    def __init__(self):
        super().__init__()
        self.d_blocks = {}

    def add_block(self, n_block):
        assert isinstance(n_block, Block)
        assert n_block.sid not in self.d_blocks

        self.d_blocks[n_block.sid] = n_block
        n_block.set_parent(self)

    def blocks(self):
        for blk_id in sorted(self.d_blocks):
            yield self.d_blocks[blk_id]

    def dump_hierarchy(self, indent=0):
        print(" " * indent, "System")
        for n_block in self.blocks():
            n_block.dump_hierarchy(indent + 1)

    def iter_all_blocks(self):
        for n_block in self.d_blocks.values():
            yield from n_block.iter_all_blocks()


class Block(Node):
    def __init__(self, sid, name, kind):
        assert isinstance(sid, str), "expected string, got %s" % type(sid)
        assert isinstance(name, str)
        assert isinstance(kind, str)

        super().__init__()

        self.sid  = sid
        self.name = name
        self.kind = kind

    def dump_hierarchy(self, indent=0):
        print(" " * indent, "Block %s (%s)" % (self.kind, repr(self.name)))

    def set_parent(self, n_parent):
        assert isinstance(n_parent, System)
        super().set_parent(n_parent)

    def get_container(self):
        ptr = self.n_parent
        while not isinstance(ptr, Container):
            ptr = ptr.n_parent
        return ptr

    def full_name(self):
        # Gets the full name for this block, including the model's
        # name. E.g. Test1/SubSystem/MyBlock
        name_stack = []
        ptr = self
        while ptr:
            if isinstance(ptr, Container):
                name_stack.append(ptr.name)
            elif isinstance(ptr, Block):
                name_stack.append(ptr.name)
            ptr = ptr.n_parent
        return "/".join(reversed(name_stack))

    def local_name(self):
        # Gets the name for this block, local to the
        # model. E.g. SubSystem/MyBlock.
        name_stack = []
        ptr = self
        while ptr:
            if isinstance(ptr, Container):
                break
            elif isinstance(ptr, Block):
                name_stack.append(ptr.name)
            ptr = ptr.n_parent
        return "/".join(reversed(name_stack))

    def loc(self):
        return Location(self.get_container().filename,
                        blockname = self.local_name())

    def iter_all_blocks(self):
        yield self


class Sub_System(Block):
    def __init__(self, sid, name, n_system):
        super().__init__(sid, name, "SubSystem")
        assert isinstance(n_system, System)

        self.n_system = n_system
        self.n_system.set_parent(self)

    def dump_hierarchy(self, indent=0):
        print(" " * indent, "Block %s (%s)" % (self.kind, repr(self.name)))
        self.n_system.dump_hierarchy(indent + 1)

    def iter_all_blocks(self):
        yield self
        yield from self.n_system.iter_all_blocks()


class Matlab_Function(Block):
    # In Simulink this is actually a magic Subsystem that you cannot
    # enter, that contains an S-Function block referencing a Stateflow
    # MATLAB function. We hide this as well, but in a different way:
    # we pretend it's a distinct top-level object (and not a special
    # kind of sub-system).
    def __init__(self, sid, name, sref):
        super().__init__(sid, name, "SubSystem")
        assert isinstance(sref, Source_Reference)

        self.sref = sref

    def get_encoding(self):
        n_container = self.get_container()
        return n_container.encoding

    def get_text(self):
        return self.sref.get_text()

    def set_text(self, text):
        assert isinstance(text, str)
        self.sref.set_text(text)

    def dump_hierarchy(self, indent=0):
        print(" " * indent, "Block %s (%s)" % ("L2MatlabFunction",
                                               repr(self.name)))
        lines = self.get_text().rstrip().splitlines()
        print(" " * indent, "-" * 60)
        for line in lines:
            print(" " * indent, ("| %s" % line).rstrip())
        print(" " * indent, "-" * 60)


class Link(Node):
    # This is a semantically important connection between two or more
    # blocks.

    # pylint: disable=abstract-method
    pass


class Annotation(Node):
    # This is a text annotation, i.e. a comment. It doesn't do
    # anything, but we're going to use them to justify miss_hit
    # messages.

    # pylint: disable=abstract-method
    pass


class Connector(Node):
    # This is a line, but it doesn't do anything, i.e. a comment. It
    # is used to connect an annotation to some block.

    # pylint: disable=abstract-method
    pass
