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

"""
This is a minimal parser for SIMULINK models (currently only the
new style slx models, support for old style mdl files will come
later).
"""

import os.path
import zipfile
import xml.etree.ElementTree as ET

from abc import ABCMeta, abstractmethod

from miss_hit_core.config import Config
from miss_hit_core.s_ast import *
from miss_hit_core.errors import Message_Handler, ICE

# pylint: disable=invalid-name
anatomy = {}
# pylint: enable=invalid-name


class Simulink_Parser(metaclass=ABCMeta):
    def __init__(self, mh, filename, cfg):
        assert isinstance(mh, Message_Handler)
        assert isinstance(filename, str)
        assert isinstance(cfg, Config)

        self.mh       = mh
        self.filename = filename
        self.cfg      = cfg
        # Basic properties

    @abstractmethod
    def parse_file(self):
        pass

    @abstractmethod
    def save_and_close(self):
        pass


class Simulink_SLX_Parser(Simulink_Parser):
    def __init__(self, mh, filename, cfg):
        super().__init__(mh, filename, cfg)

        self.xml_blockdiagram   = None
        self.xml_stateflow      = None
        self.xml_coreproperties = None
        # ETree nodes for the relevant files

        self.other_content = {}
        with zipfile.ZipFile(self.filename) as zfd:
            for name in zfd.namelist():
                with zfd.open(name) as fd:
                    if name == "metadata/coreProperties.xml":
                        self.xml_coreproperties = ET.parse(fd)
                    elif name == "simulink/blockdiagram.xml":
                        self.xml_blockdiagram = ET.parse(fd)
                    elif name == "simulink/stateflow.xml":
                        self.xml_stateflow = ET.parse(fd)
                    else:
                        self.other_content[name] = fd.read()
        # Read entire zipfile, storing content here. The two XML files
        # we're interested in we already parse with ETree. The rest of
        # the parsing happens in parse_file.

        self.sf_names = {}
        # Dictionary for Stateflow items mapping from string names to
        # ET.Element nodes for the Stateflow charts.

        self.is_external_harness = False
        # Set to true once if we determine that this an external
        # harness. An external harness requires the main model to be
        # used sensibly. In particular any MATLAB functions referenced
        # from the main model likely won't be present in its own
        # Stateflow file.
        #
        # For now we basically ignore external harnesses.

        self.name_stack = []
        # As we go deeper into a model, we need to know the full chain
        # of subsystem names. Althought the tree eventually contains
        # this information, we don't have all the links set up during
        # parsing.

    ######################################################################
    # Generic functions
    ######################################################################

    @staticmethod
    def parse_p_tags(et_item):
        assert isinstance(et_item, ET.Element)

        properties = {}

        for et_child in et_item:
            if et_child.tag == "P":
                properties[et_child.attrib["Name"]] = et_child.text

        return properties

    def parse_file(self):
        # Parse stateflow XML first, since we want to refer to it from
        # the blockdiagram.
        if self.xml_stateflow:
            self.parse_stateflow(self.xml_stateflow.getroot())

        # Parse blockdiagram and return the AST.
        return self.parse_blockdiagram(self.xml_blockdiagram.getroot())

    def save_and_close(self):
        # Write back the (potentially modified) tree.
        with zipfile.ZipFile(self.filename, mode="w") as zfd:
            if self.xml_blockdiagram:
                with zfd.open("simulink/blockdiagram.xml", mode="w") as fd:
                    self.xml_blockdiagram.write(fd)
            if self.xml_stateflow:
                with zfd.open("simulink/stateflow.xml", mode="w") as fd:
                    self.xml_stateflow.write(fd)
            if self.xml_coreproperties:
                with zfd.open("metadata/coreProperties.xml", mode="w") as fd:
                    self.xml_coreproperties.write(fd)
            for name in sorted(self.other_content):
                with zfd.open(name, mode="w") as fd:
                    fd.write(self.other_content[name])

    def loc(self):
        return Location(self.filename,
                        blockname = "/".join(self.name_stack))

    ######################################################################
    # Stateflow parsing
    ######################################################################

    def parse_stateflow(self, et_stateflow):
        assert isinstance(et_stateflow, ET.Element)
        assert et_stateflow.tag == "Stateflow"

        d_instances = {}
        # A dictionary for name_str -> (machine, chart)

        d_machines  = {}
        # A dictionary for machine_id -> chart_id -> etree

        for et_item in et_stateflow:
            if et_item.tag == "machine":
                item_id = int(et_item.attrib["id"])
                d_machines[item_id] = self.parse_machine(et_item)
            elif et_item.tag == "instance":
                name, info = self.parse_instance(et_item)
                d_instances[name] = info
            else:
                self.mh.error(self.loc(),
                              "unknown top-level stateflow item %s" %
                              et_item.tag)

        for name in d_instances:
            machine_id, chart_id = d_instances[name]
            self.sf_names[name] = d_machines[machine_id][chart_id]

    def parse_instance(self, et_instance):
        assert isinstance(et_instance, ET.Element)
        assert et_instance.tag == "instance"

        props = self.parse_p_tags(et_instance)

        # Sanity check we have nothing but properties
        for et_item in et_instance:
            if et_item.tag != "P":
                self.mh.error(self.loc(),
                              "unknown item %s in instance" % et_item.tag)

        return props["name"], (int(props["machine"]),
                               int(props["chart"]))

    def parse_machine(self, et_machine):
        assert isinstance(et_machine, ET.Element)
        assert et_machine.tag == "machine"

        d_machine = {}

        # We expect to have a single tag called 'Children'.
        et_children = None
        for et_item in et_machine:
            if et_item.tag == "P":
                pass
            elif et_item.tag == "Children":
                if et_children:
                    raise ICE("multiple children in Stateflow machine")
                et_children = et_item
            elif et_item.tag == "debug":
                # TODO: Unclear what the presence of this does. To
                # investigate.
                pass
            else:
                self.mh.error(self.loc(),
                              "Unknown item %s in machine" % et_item.tag)

        for et_item in et_children:
            if et_item.tag == "target":
                # TODO: Unclear what exactly this does right now.
                pass
            elif et_item.tag == "chart":
                chart_id = int(et_item.attrib["id"])
                d_machine[chart_id] = et_item
            else:
                self.mh.error(self.loc(),
                              "Unknown item %s in Children" % et_item.tag)

        return d_machine

    ######################################################################
    # Simulink parsing
    ######################################################################

    def parse_block_matlab_function(self, et_block, props):
        assert isinstance(et_block, ET.Element)
        assert isinstance(props, dict)
        assert et_block.tag == "Block"
        assert et_block.attrib["BlockType"] == "SubSystem"
        assert props.get("SFBlockType", None) == "MATLAB Function"
        assert not self.is_external_harness

        # To find the program text for this, we need to look into the
        # Stateflow XML. First we construct a name by chaining
        # together all system names (except the top-level one) with /.
        sf_base_name = "/".join(self.name_stack + [et_block.attrib["Name"]])

        # Get Stateflow chart
        if sf_base_name in self.sf_names:
            et_chart = self.sf_names[sf_base_name]
        else:
            self.mh.error(self.loc(),
                          "Could not find %s in Stateflow" % sf_base_name)

        # Quickly rifle through Children to find the relevant eml
        # block. This could be more structured, and should be if we do
        # more stateflow support in the future.
        is_eml    = False
        et_script = None
        for et_eml in et_chart.find("Children").iter("eml"):
            for et_item in et_eml:
                if et_item.tag == "P":
                    if et_item.attrib["Name"] == "isEML":
                        is_eml = bool(et_item.text)
                    elif et_item.attrib["Name"] == "script":
                        if et_script:
                            raise ICE("multiple scripts in eml tag")
                        et_script = et_item
                else:
                    self.mh.error(self.loc(),
                                  "Unexpected child %s of eml" % et_item.tag)
                if et_script and not is_eml:
                    raise ICE("script found, but isEML is not true")
        if et_script is None:
            raise ICE("referenced script for %s not found" % sf_base_name)

        return Matlab_Function(et_block.attrib["SID"],
                               et_block.attrib["Name"],
                               SLX_Reference(et_script))

    def parse_block_subsystem(self, et_block):
        assert isinstance(et_block, ET.Element)
        assert et_block.tag == "Block"
        assert et_block.attrib["BlockType"] == "SubSystem"

        n_system    = None
        system_name = et_block.attrib["Name"]

        props = self.parse_p_tags(et_block)

        if props.get("SFBlockType", None) == "MATLAB Function":
            # This could be a special "MATLAB Function" sub-system, in
            # which case we special case
            n_block = self.parse_block_matlab_function(et_block, props)

        else:
            # This is a normal sub-system. First we're finding the system
            # nested.
            for et_item in et_block:
                if et_item.tag == "System":
                    if n_system:
                        raise ICE("multiple systems in subsytem")
                    self.name_stack.append(system_name)
                    n_system = self.parse_system(et_item)
                    self.name_stack.pop()

            # Then we build a sub-system block referencing the system
            n_block = Sub_System(et_block.attrib["SID"],
                                 system_name,
                                 n_system)

        return n_block

    def parse_block(self, et_block):
        assert isinstance(et_block, ET.Element)
        assert et_block.tag == "Block"

        block_type = et_block.attrib["BlockType"]

        # Debug: Maintain anatomy

        if block_type not in anatomy:
            anatomy[block_type] = set()
        for et_child in et_block:
            if et_child.tag not in ("P", "Port"):
                anatomy[block_type].add(et_child.tag)

        # Parse block

        if block_type == "SubSystem":
            n_block = self.parse_block_subsystem(et_block)
        else:
            # Some other generic block
            n_block = Block(et_block.attrib["SID"],
                            et_block.attrib["Name"],
                            block_type)

        return n_block

    def parse_system(self, et_system):
        assert isinstance(et_system, ET.Element)
        assert et_system.tag == "System"

        n_system = System()

        block_items = []
        line_items = []
        anno_items = []

        # First we go over all items, but we need to process them in a
        # sensible order...
        for et_item in et_system:
            if et_item.tag == "P":
                continue
            elif et_item.tag == "Block":
                block_items.append(et_item)
            elif et_item.tag == "Line":
                line_items.append(et_item)
            elif et_item.tag == "Annotation":
                anno_items.append(et_item)
            elif et_item.tag == "Connector":
                pass
            else:
                self.mh.error(self.loc(),
                              "Unknown child %s in system" % et_item.tag)

        # Blocks first
        for et_block in block_items:
            n_block = self.parse_block(et_block)
            n_system.add_block(n_block)

        return n_system

    def parse_model(self, et_model):
        assert isinstance(et_model, ET.Element)
        assert et_model.tag == "Model"

        n_model = Model(self.filename)

        n_system = None

        for et_item in et_model:
            if et_item.tag == "System":
                if n_system:
                    raise ICE("multiple systems in Model")
                n_system = self.parse_system(et_item)

        n_model.set_system(n_system)

        return n_model

    def parse_library(self, et_library):
        assert isinstance(et_library, ET.Element)
        assert et_library.tag == "Library"

        n_library = Library(self.filename)

        n_system = None

        for et_item in et_library:
            if et_item.tag == "System":
                if n_system:
                    raise ICE("multiple systems in Library")
                n_system = self.parse_system(et_item)

        n_library.set_system(n_system)

        return n_library

    def parse_blockdiagram(self, et_node):
        assert isinstance(et_node, ET.Element)
        assert et_node.tag == "ModelInformation"

        top_object = None

        props = self.parse_p_tags(et_node)

        if "HarnessUUID" in props:
            self.is_external_harness = True

            # TODO: We do not yet support this, so just return
            # nothing.
            return None

        # Sometimes we can have the stateflow file embedded in the
        # diagram. In this case we need to make sure to parse it
        # first.
        for item in et_node:
            if item.tag == "Stateflow":
                self.parse_stateflow(item)

        for item in et_node:
            if item.tag == "Model":
                if top_object:
                    self.mh.error(self.loc(),
                                  "more than one model/library in file")
                top_object = self.parse_model(item)
            elif item.tag == "Library":
                if top_object:
                    self.mh.error(self.loc(),
                                  "more than one model/library in file")
                top_object = self.parse_library(item)
            elif item.tag == "Stateflow":
                pass
            else:
                self.mh.error(self.loc(),
                              "I do not understand top-level item %s" %
                              item.tag)

        # Set encoding on top-level container
        if "SavedCharacterEncoding" in props:
            top_object.set_encoding(props["SavedCharacterEncoding"])

        return top_object


def sanity_test(mh, filename, _):
    # pylint: disable=import-outside-toplevel
    from miss_hit_core import m_lexer
    # pylint: enable=import-outside-toplevel

    print("=== Parsing %s ===" % filename)

    mh.register_file(filename)
    slp = Simulink_SLX_Parser(mh, filename, Config())

    if slp.is_external_harness:
        print("   > Ignored external harness")
        return

    n_container = slp.parse_file()

    # Dump lexing of matlab blocks
    for n_block in n_container.iter_all_blocks():
        if not isinstance(n_block, Matlab_Function):
            continue

        mh.info(n_block.loc(),
                "block contains %u lines of MATLAB" %
                len(n_block.get_text().splitlines()))
        lexer = m_lexer.MATLAB_Lexer(mh,
                                     n_block.get_text(),
                                     filename,
                                     n_block.local_name())
        while True:
            token = lexer.token()
            if token is None:
                break
            mh.info(token.location, token.kind)
    mh.finalize_file(filename)

    # Dump model hierarchy
    n_container.dump_hierarchy()


def main():
    # pylint: disable=import-outside-toplevel
    from argparse import ArgumentParser
    # pylint: enable=import-outside-toplevel

    ap = ArgumentParser()
    ap.add_argument("name", metavar="FILE|DIR")
    options = ap.parse_args()

    mh = Message_Handler("debug")
    mh.sort_messages = False
    mh.colour        = False

    if os.path.isfile(options.name):
        sanity_test(mh, options.name, options)
    elif os.path.isdir(options.name):
        for path, _, files in os.walk(options.name):
            for f in files:
                if f.endswith(".slx"):
                    sanity_test(mh, os.path.join(path, f), options)
    else:
        ap.error("%s is neither a file or directory" % options.name)

    print()
    print("=== Summary of misc. children ===")
    for block_type in sorted(anatomy):
        print("Children in %s" % block_type)
        for tag in sorted(anatomy[block_type]):
            print("   * %s" % tag)

    mh.summary_and_exit()


if __name__ == "__main__":
    main()
