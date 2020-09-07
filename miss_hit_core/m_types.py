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

# Some helpful links:
#
# Basic overview:
# https://uk.mathworks.com/help/matlab/matlab_prog/fundamental-matlab-classes.html
#
# Implicit conversion within arrays:
# https://uk.mathworks.com/help/matlab/matlab_prog/valid-combinations-of-unlike-classes.html

class Type:
    """ Root class for type system. """
    def __init__(self):
        self.ty_parent = None
        # For subtypes this identifies our parent type

    def set_parent(self, ty_parent):
        assert isinstance(ty_parent, Type)
        self.ty_parent = ty_parent


class Array_Type(Type):
    """N-dimensional arrays

    Pretty much everything (instances of Fundamental_Type) in MATLAB
    can be an array. Arrays can have any number of dimensions. Actual
    sizes can be static or dynamic, and can be zero.

    All indices start at 1 and are always integers.

    Side-note: you can also index an array with the logical 'false',
    but it doesn't do anything (it returns the empty array, and when
    setting doesn't change anything). This also applies to cell
    arrays.

    """


class Fundamental_Type(Type):
    """Types that can become n-dimensional arrays"""


class Scalar_Type(Type):
    """Types that cannot become an n-dimensional array"""


class Function_Pointer_Type(Scalar_Type):
    """Function handles using the @ operator"""


class Fundamental_Scalar_Type(Fundamental_Type):
    """MISS_HIT distinguishes between machine types and structured data"""


class Fundamental_Composite_Type(Fundamental_Type):
    """MISS_HIT distinguishes between machine types and structured data"""


class Logical_Type(Fundamental_Scalar_Type):
    """Boolean"""


class String_Type(Fundamental_Scalar_Type):
    """Strings, double quoted (MATLAB only)"""


class Character_Type(Fundamental_Scalar_Type):
    """Single character

    Single-quoted strings (and also double-quoted strings in Octave)
    are really character arrays.

    """


class Numeric_Type(Fundamental_Scalar_Type):
    """Numbers"""


class Integer_Type(Numeric_Type):
    """Signed and unsigned integers"""


class Signed_Integer_Type(Integer_Type):
    """Signed integers"""


class Unsigned_Integer_Type(Integer_Type):
    """Unsigned integers, does not have modular behaviour in MATLAB"""


class Floating_Point_Type(Numeric_Type):
    """Floats"""


# Table not supported yet


class Cell_Type(Fundamental_Composite_Type):
    """Cell arrays"""


class Structure_Type(Fundamental_Composite_Type):
    """Dynamic and static structures"""


class Class_Type(Fundamental_Composite_Type):
    """User-defined classes"""
