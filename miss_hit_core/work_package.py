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

import os.path

from miss_hit_core import s_ast
from miss_hit_core import cfg_tree

from miss_hit_core.errors import Message_Handler, ICE, Location


class Work_Package:
    def __init__(self, filename, mh, options, extra_options):
        assert isinstance(filename, str)
        assert isinstance(mh, Message_Handler)

        self.filename      = os.path.normpath(filename)
        self.mh            = mh
        self.cfg           = None
        self.options       = options
        self.extra_options = extra_options
        self.modified      = False

    def write_modified(self, content):
        raise ICE("somhow called root class method")


class SIMULINK_File_WP(Work_Package):
    # This is a SIMULINK model that will in turn spawn multiple
    # Embedded_MATLAB_WP instances.
    def __init__(self, filename, mh, options, extra_options):
        super().__init__(filename, mh, options, extra_options)
        self.cfg = cfg_tree.get_config(self.filename)

    def write_modified(self, content):
        raise ICE("logic error - must not be called for SL File WP")

    def register_file(self):
        self.mh.register_file(self.filename)


class MATLAB_Work_Package(Work_Package):
    # This is an abstract base class of a WP that contains some actual
    # MATLAB code. This is what will be fed to each tool.
    def __init__(self,
                 filename, blockname,
                 encoding,
                 mh, options, extra_options):
        super().__init__(filename, mh, options, extra_options)

        assert isinstance(encoding, str)
        assert blockname is None or isinstance(blockname, str)

        self.blockname = blockname
        self.encoding  = encoding

    def get_content(self):
        raise ICE("somhow called root class method")

    def register_file(self):
        self.mh.register_file(self.filename)


class MATLAB_File_WP(MATLAB_Work_Package):
    # MATLAB code that is in an m-file somewhere
    def __init__(self, filename,
                 encoding,
                 mh, options, extra_options):
        super().__init__(filename, None,
                         encoding,
                         mh, options, extra_options)
        self.cfg = cfg_tree.get_config(self.filename)

    def write_modified(self, content):
        assert isinstance(content, str)
        self.modified = True
        with open(self.filename, "w", encoding=self.encoding) as fd:
            fd.write(content)

    def get_content(self):
        # First we try to read the file with the suggested encoding.
        try:
            with open(self.filename, "r", encoding=self.encoding) as fd:
                return fd.read()
        except UnicodeDecodeError:
            pass

        if self.encoding.lower() == "utf-8":
            # If that was UTF-8, we give up and ask for help.
            self.mh.error(
                Location(self.filename),
                "encoding error, please specify correct encoding"
                " on using --input-encoding",)
        else:
            # Otherwise, we issue a warning, and try once more with
            # UTF-8.
            self.mh.warning(
                Location(self.filename),
                "encoding error for %s, assuming utf-8 instead" %
                self.encoding)
            self.encoding = "utf-8"

        try:
            with open(self.filename, "r", encoding=self.encoding) as fd:
                return fd.read()
        except UnicodeDecodeError:
            self.mh.error(
                Location(self.filename),
                "encoding error, please specify correct encoding"
                " on using --input-encoding",)


class Embedded_MATLAB_WP(MATLAB_Work_Package):
    # MATLAB code that is embedded in a slx-file somewhere
    def __init__(self, simulink_wp, simulink_block):
        assert isinstance(simulink_wp, SIMULINK_File_WP)
        assert isinstance(simulink_block, s_ast.Matlab_Function)

        n_container = simulink_block.get_container()

        super().__init__(n_container.filename,
                         simulink_block.local_name(),
                         simulink_block.get_encoding(),
                         simulink_wp.mh.fork(),
                         simulink_wp.options,
                         simulink_wp.extra_options)

        self.cfg         = simulink_wp.cfg
        self.block       = simulink_block
        self.simulink_wp = simulink_wp

    def write_modified(self, content):
        assert isinstance(content, str)
        self.modified = True
        self.simulink_wp.modified = True
        self.block.set_text(content)

    def get_content(self):
        return self.block.get_text()


class Result:
    def __init__(self, wp, processed):
        assert isinstance(wp, Work_Package)
        assert isinstance(processed, bool)
        self.wp        = wp
        self.processed = processed


def create(filename, default_encoding, mh, options, extra_options):
    if filename.endswith(".m"):
        return MATLAB_File_WP(filename, default_encoding,
                              mh.fork(), options, extra_options)

    elif filename.endswith(".slx"):
        return SIMULINK_File_WP(filename,
                                mh.fork(), options, extra_options)
