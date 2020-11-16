#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2020, Florian Schanda                         ##
##              Copyright (C) 2020, Veoneer Sweden AB                       ##
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

# We have some assets we want to use when generating e.g. HTML
# reports. We could just hotlink, but this seems like a privacy
# invasion; so instead we try to find these assets locally.

# There are three scenarios as to how MISS_HIT can be installed:
#   1. As a PyPI package (the recommended way)
#   2. As a canned copy of the github repo (useful for some companies)
#   3. As a developer checkout (how we run the test-suite)

# This horrific package aims to make available one URL that makes this
# entirely transparent to the rest of MISS_HIT.

import sys
import os

# pylint: disable=bare-except

PORTABLE_RES_URL = "https://florianschanda.github.io/miss_hit"

try:
    import pkg_resources

    # Fetch resource. This is option 1 above.
    RES_URL = pkg_resources.resource_filename("miss_hit_core",
                                              "resources/style.css")

    # We need to check this actually exists. Older installs could mask
    # option 2 or 3.
    if not os.path.isfile(RES_URL):
        raise Exception

    # Normalise and turn into an URL
    RES_URL = "file://%s" % os.path.dirname(RES_URL).replace("\\", "/")

except:  # noqa
    # Fallback approach for option 2 or 3. We try to find style.css
    # relative to the executable we're using.
    RES_URL = os.path.join(sys.path[0], "docs", "style.css")
    RES_URL = os.path.dirname(RES_URL).replace("\\", "/")

    # If this doesn't exits (likely option 2), fallback even more to
    # the github URL.
    if os.path.isdir(RES_URL):
        RES_URL = "file://%s" % RES_URL
    else:
        RES_URL = PORTABLE_RES_URL
