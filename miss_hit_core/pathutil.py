#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2021, Florian Schanda                         ##
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

# There are some interesting bugs in some Windows environments. This
# library attmpets to work around some of them.
#
# Specifically the behaviour of os.path.abspath is funny. When called with
# "foo/" the answers are as follows:
# * In Linux, we get "/potato/foo"
# * In Windows, we get "C:\potato\foo"
# * In Windows, under git bash, we get "C:\potato\foo\"
#
# This causes issues with cfg_tree, and sometimes the same config
# files is parsed twice, leading to confusing errors.

import os


def abspath(path):
    assert isinstance(path, str)
    return os.path.normpath(os.path.join(os.getcwd(), path))
