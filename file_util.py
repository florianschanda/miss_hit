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

from errors import Location, Error, Message_Handler


def load_local_file(mh, filename, encoding="utf-8"):
    assert isinstance(mh, Message_Handler)
    assert isinstance(filename, str)
    assert isinstance(encoding, str)

    mh.register_file(filename)

    try:
        if not os.path.exists(filename):
            mh.error(Location(filename), "file does not exist")

        if not os.path.isfile(filename):
            mh.error(Location(filename), "is not a file")
    except Error:
        return None

    try:
        with open(filename, encoding=encoding) as fd:
            content = fd.read()
    except UnicodeDecodeError:
        if encoding != "utf-8":
            with open(filename, encoding="utf-8") as fd:
                content = fd.read()
        else:
            content = None

    return content
