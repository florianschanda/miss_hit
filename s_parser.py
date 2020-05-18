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

import xml.etree.ElementTree as ET
import os.path
import zipfile

from errors import ICE, Error, Location, Message_Handler


class SIMULINK_Block:
    def __init__(self, model, name):
        assert isinstance(model, SIMULINK_Model)
        assert isinstance(name, str)

        self.model = model
        # A link back to the model(file) containing this block

        self.name = name
        # Full name that can be used to identify the block/function in
        # error messages. Should be something like
        # filename/subsystem/blockname

    def full_name(self):
        """ Returns the full name for this block """
        return self.name

    def local_name(self):
        """ Returns a shorter name for this block

        For example if the full name is "test1/myblock/potato" then the short
        name is "myblock/potato".
        """
        return self.name[len(self.model.modelname) + 1:]

    def loc(self):
        return Location(self.model.filename,
                        blockname = self.local_name())


class SIMULINK_MATLAB_Block(SIMULINK_Block):
    """Represents a SIMULINK "MATLAB Function" block.

    This block contains MATLAB code directly embedded inside the
    SIMULINK model, which should be processed by MISS_HIT.
    """
    def __init__(self, model, name, xml_root_code):
        super().__init__(model, name)
        assert isinstance(xml_root_code, ET.Element)
        assert xml_root_code.tag == "P"

        self.xml_root_code = xml_root_code
        # Pointer to the P tag containing the actual script

    def get_text(self):
        return self.xml_root_code.text

    def set_text(self, text):
        assert isinstance(text, str)
        self.xml_root_code.text = text

    def get_encoding(self):
        # HACK for now, this can be found in the actual model
        return "utf-8"


class SIMULINK_Model:
    """Represents a SIMULINK file/model.

    A modern SIMULINK model is just a zip file containing undocumented
    XML. This is a very high level and incomplete interface to the
    information contained within; just enough to process embedded
    scripts for now.
    """
    def __init__(self, mh, filename):
        assert isinstance(mh, Message_Handler)
        assert isinstance(filename, str)
        assert filename.endswith(".slx")

        self.mh = mh

        self.filename = filename
        # The actual file-name

        self.modelname = os.path.basename(filename).replace(".slx", "")
        # The model name is the base filename with the extension
        # stripped.

        self.other_content      = {}
        self.xml_blockdiagram   = None
        self.xml_stateflow      = None
        self.xml_coreproperties = None
        # There are three XML files of particular interest:
        #
        #   * the core properties contain version information and a
        #     "last updated" field we might want to change
        #
        #   * the blockdiagram contains all blocks and subsystems, but
        #     does not contain any embedded code
        #
        #   * the stateflow file contains embedded code

        self.matlab_blocks = []
        # A list of SIMULINK_MATLAB_Blocks

        # Read all files, and parse three we care about. The rest we
        # need to save as well, since we might have to re-create the
        # zip file again if we write any changes.
        with zipfile.ZipFile(self.filename) as zf:
            for name in zf.namelist():
                with zf.open(name) as fd:
                    if name == "metadata/coreProperties.xml":
                        self.xml_coreproperties = ET.parse(fd)
                    elif name == "simulink/blockdiagram.xml":
                        self.xml_blockdiagram = ET.parse(fd)
                    elif name == "simulink/stateflow.xml":
                        self.xml_stateflow = ET.parse(fd)
                    else:
                        self.other_content[name] = fd.read()

        # Parse blocks. If there is no stateflow file, there won't be
        # any embedded code, so there is nothing to do in that case.
        if self.xml_stateflow is not None:
            self.parse_root()

    def loc(self):
        return Location(self.filename)

    def save_and_close(self):
        with zipfile.ZipFile(self.filename, mode="w") as zf:
            with zf.open("simulink/stateflow.xml", mode="w") as fd:
                self.xml_stateflow.write(fd)
            with zf.open("simulink/blockdiagram.xml", mode="w") as fd:
                self.xml_blockdiagram.write(fd)
            with zf.open("metadata/coreProperties.xml", mode="w") as fd:
                self.xml_coreproperties.write(fd)
            for name in self.other_content:
                with zf.open(name, mode="w") as fd:
                    fd.write(self.other_content[name])

    @staticmethod
    def _get_properties(xml_node):
        """Gets a dictionary of all property tags, as strings."""
        assert isinstance(xml_node, ET.Element)
        return {prop.attrib["Name"]: prop.text
                for prop in xml_node.findall("P")}

    @staticmethod
    def _get_properties_with_node(xml_node):
        """Gets a dictionary of all property tags, as tuples.

        The tuple contains the property text and its node."""
        assert isinstance(xml_node, ET.Element)
        return {prop.attrib["Name"]: (prop.text, prop)
                for prop in xml_node.findall("P")}

    def parse_root(self):
        root = self.xml_blockdiagram.getroot()
        system = None
        for mdl in root:
            if mdl.tag not in ("Model", "Library"):
                continue

            m_props = self._get_properties(mdl)

            if "HarnessUUID" in m_props:
                self.mh.info(self.loc(), "skipping externally saved harness")
                continue

            if system is not None:
                raise ICE("%s contains both a model and library" %
                          self.filename)

            system = mdl.findall("System")
            if len(system) != 1:
                raise ICE("%s contains more than one top-level system" %
                          self.filename)
            system = system[0]

            self.parse_system(self.modelname,
                              system)

    def parse_matlab_block(self, function_name):
        assert self.xml_stateflow is not None
        assert isinstance(function_name, str)

        # Produce shortened block name, which used to index into the
        # stateflow xml
        sf_name = function_name[len(self.modelname) + 1:]

        root = self.xml_stateflow.getroot()
        machine_id = None
        chart_id = None
        for instance in root.findall("instance"):
            i_props = self._get_properties(instance)
            if i_props.get("name", None) == sf_name:
                chart_id = int(i_props["chart"])
                machine_id = int(i_props["machine"])
        if chart_id is None:
            raise ICE("could not find any matching chart_id in for %s" %
                      sf_name)

        chart_xml = None
        for machine in root.findall("machine"):
            if int(machine.attrib["id"]) != machine_id:
                continue

            for chart in machine.find("Children").findall("chart"):
                if int(chart.attrib["id"]) != chart_id:
                    continue

                chart_xml = chart
                break

            if chart_xml:
                break
        if chart_xml is None:
            raise ICE("could not find any chart node %u in %s" %
                      (chart_id, self.modelname))

        matlab_block = None
        for eml in chart_xml.find("Children").iter("eml"):
            eml_props = self._get_properties_with_node(eml)
            if not bool(eml_props["isEML"][0]):
                raise ICE("eml block for %s does not have isEML property set" %
                          sf_name)
            if matlab_block is not None:
                raise ICE("found more than one script tag for %s" %
                          sf_name)

            matlab_block = SIMULINK_MATLAB_Block(self,
                                                 function_name,
                                                 eml_props["script"][1])

        self.matlab_blocks.append(matlab_block)

    def parse_system(self, system_name, system_tree):
        assert isinstance(system_name, str)
        assert isinstance(system_tree, ET.Element)

        for block in system_tree.findall("Block"):
            b_name = block.attrib["Name"]
            b_props = self._get_properties(block)

            # Check if this block is an embedded MATLAB function
            if b_props.get("SFBlockType", None) == "MATLAB Function":
                self.parse_matlab_block(system_name + "/" + b_name)

            # Recuse into nested systems
            for sub_system in block.findall("System"):
                self.parse_system(system_name + "/" + b_name,
                                  sub_system)


def sanity_test(mh, filename, show_bt):
    # pylint: disable=import-outside-toplevel
    import traceback
    import m_lexer
    # pylint: enable=import-outside-toplevel

    try:
        mh.register_file(filename)
        smdl = SIMULINK_Model(mh, filename)
        mh.info(smdl.loc(),
                "model contains %u MATLAB function blocks" %
                len(smdl.matlab_blocks))

        for block in smdl.matlab_blocks:
            mh.info(block.loc(),
                    "block contains %u lines of MATLAB" %
                    len(block.get_text().splitlines()))
            lexer = m_lexer.MATLAB_Lexer(mh,
                                         block.get_text(),
                                         filename,
                                         block.local_name())
            while True:
                token = lexer.token()
                if token is None:
                    break
                mh.info(token.location, token.kind)

    except Error:
        if show_bt:
            traceback.print_exc()

    except ICE as ice:
        if show_bt:
            traceback.print_exc()
        print("ICE:", ice.reason)

    mh.finalize_file(filename)


def sanity_test_main():
    # pylint: disable=import-outside-toplevel
    from argparse import ArgumentParser
    # pylint: enable=import-outside-toplevel
    ap = ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--no-tb",
                    action="store_true",
                    default=False,
                    help="Do not show debug-style backtrace")
    options = ap.parse_args()

    mh = Message_Handler("debug")
    mh.sort_messages = False
    mh.colour = False

    sanity_test(mh,
                options.file,
                not options.no_tb)

    mh.summary_and_exit()


if __name__ == "__main__":
    sanity_test_main()
