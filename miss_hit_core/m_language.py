#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2022, Florian Schanda                         ##
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

import re


class Language:
    def __init__(self, name):
        assert isinstance(name, str)
        self.name = name

        self.token_kinds = set([
            "NEWLINE",
            "CONTINUATION",
            "COMMENT",
            "IDENTIFIER",
            "NUMBER",
            "CARRAY",          # 'foo' character array
            "STRING",          # "foo" string class literal
            "KEYWORD",         # see below
            "OPERATOR",        # see docs/internal/matlab_operators.txt
            "COMMA",           # ,
            "SEMICOLON",       # ;
            "COLON",           # :
            "BRA", "KET",      # ( )
            "C_BRA", "C_KET",  # { }
            "M_BRA", "M_KET",  # [ ] for matrices
            "A_BRA", "A_KET",  # [ ] for assignment targets
            "ASSIGNMENT",      # =
            "SELECTION",       # .
            "AT",              # @
            "BANG",            # !
            "METACLASS",       # ?
            "ANNOTATION",      # miss_hit annotation
        ])

        self.tokens_with_implicit_value = set([
            "COMMA",
            "SEMICOLON",
            "COLON",
            "BRA", "KET",      # ( )
            "C_BRA", "C_KET",  # { }
            "M_BRA", "M_KET",  # [ ] for matrices
            "A_BRA", "A_KET",  # [ ] for assignment targets
            "ASSIGNMENT",
            "SELECTION",
            "AT",
            "METACLASS"
        ])
        assert self.tokens_with_implicit_value <= self.token_kinds
        # Token kinds, and also a subset for the tokens where there is
        # no value (e.g. BRA).

        self.keywords = set()
        # Base keywords

        self.class_keywords = set()
        # Keywords that are keywords inside classdef regions only (a
        # particularly frustrating MATLAB misfeature)

        self.function_contract_keywords = set()
        # The arguments block that can appear in newer MATLAB versions

        self.annotation_keywords = set([
            "pragma",
        ])
        # Keywords for the %| anotation language

        self.comment_chars = set("")
        # Characters that start a line comment.

        self.identifiers_starting_with_underscore = False
        # Can identifiers start with an underscore?

        self.bang_is_negation = False
        # When false, ! is a shell escape. When true, ! is boolean
        # negation.

        self.hex_literals = False
        # Language supports hex literals, e.g. 0xdeadbeef and 0b10

        self.allow_classdef_subfunctions = False
        # Allows functions trailing a classdef

        self.allow_command_form = True
        # Command form is supported

        self.has_nvp_delegate = False
        # Allow .? as a token

        self.ws_insignificant = False
        # Sometimes whitespace is significant, e.g. inside a
        # matrix. In the config file mode it is never.

        ########################
        # Grammar features

        self.string_argument_pairs = False
        # Allows writing foo(x=y) instead of foo('x', y) which is a
        # another insane idea.

        self.script_global_functions = False
        # Functions sprinkled in the middle of a script, instead of at
        # the end only.

        ########################
        # Other features
        self.octave_test_pragmas = False


class Config_Language(Language):
    def __init__(self):
        super().__init__("MISS_HIT Configuration")

        self.keywords = set([
            "disable",
            "enable",
            "enable_rule",
            "entrypoint",
            "exclude_dir",
            "global",
            "libraries",
            "library",
            "limit",
            "matlab",
            "metric",
            "octave",
            "paths",
            "project_root",
            "report",
            "suppress_rule",
            "tests",
        ])

        self.comment_chars.add("#")

        self.allow_command_form = False
        self.ws_insignificant = True


class Base_Language(Language):
    # This is the common subset of MATLAB and Octave

    def __init__(self, name):
        super().__init__(name)

        # As of MATLAB 2019b
        # See: https://www.mathworks.com/help/matlab/ref/iskeyword.html
        #
        # We have taken the liberty to make "import" a keyword, since
        # that simplifies parsing quite a bit. This does mean that you
        # can't have variables named "import".
        self.keywords = set([
            'break',
            'case',
            'catch',
            'classdef',
            'continue',
            'else',
            'elseif',
            'end',
            'for',
            'function',
            'global',
            'if',
            'otherwise',
            'parfor',
            'persistent',
            'return',
            'switch',
            'try',
            'while',

            # These really should be keywords but are not
            'import',
        ])

        self.class_keywords.add("properties")
        self.class_keywords.add("enumeration")
        self.class_keywords.add("events")
        self.class_keywords.add("methods")

        self.comment_chars.add("%")


class Base_MATLAB_Language(Base_Language):
    # This is the common subset for MATLAB. The earliest MATLAB we
    # support is 2017b.

    def __init__(self, name):
        super().__init__(name)

        self.token_kinds.add("NVP_DELEGATE")
        self.tokens_with_implicit_value.add("NVP_DELEGATE")
        self.has_nvp_delegate = True
        # .? (name value pair delegation)

        self.keywords.add("spmd")

        self.function_contract_keywords.add("arguments")

        self.allow_classdef_subfunctions = True

    @classmethod
    def parse_version(cls, version):
        if version == "latest":
            return "latest", None
        else:
            match = re.match(r"^(20\d\d)([ab])$", version)
            if match is None:
                raise ValueError("MATLAB version must be YEAR[ab],"
                                 " e.g. 2017b")
            major, minor = match.groups()
            return int(major), minor

    @classmethod
    def get_version(cls, major, minor):
        if major == "latest":
            language = MATLAB_Latest_Language()
        elif major < 2017 or (major == 2017 and
                              minor == "a"):
            raise ValueError("earliest MATLAB language supported is 2017b")
        elif major > 2022 or (major == 2022 and
                              minor == "b"):
            raise ValueError("latest MATLAB language supported is 2022a")
        elif major < 2020 or (major == 2020 and
                              minor == "a"):
            language = MATLAB_2017b_Language()
        elif major < 2021:
            language = MATLAB_2020b_Language()
        else:
            language = MATLAB_2021a_Language()
        return language


class Base_Octave_Language(Base_Language):
    # This is the common subset for Octave. The earliest octave we
    # support is ???

    def __init__(self, name):
        super().__init__(name)

        self.keywords.add("end_try_catch")
        self.keywords.add("end_unwind_protect")
        self.keywords.add("endclassdef")
        self.keywords.add("endenumeration")
        self.keywords.add("endevents")
        self.keywords.add("endfor")
        self.keywords.add("endfunction")
        self.keywords.add("endif")
        self.keywords.add("endmethods")
        self.keywords.add("endparfor")
        self.keywords.add("endproperties")
        self.keywords.add("endswitch")
        self.keywords.add("endwhile")
        self.keywords.add("unwind_protect")
        self.keywords.add("unwind_protect_cleanup")

        self.comment_chars.add("#")

        self.identifiers_starting_with_underscore = True
        self.bang_is_negation = True

        self.hex_literals = True

        self.script_global_functions = True

        self.octave_test_pragmas = True

    @classmethod
    def parse_version(cls, version):
        if version == "latest":
            return "latest", None
        else:
            match = re.match(r"^(\d+)\.(\d+)$", version)
            if match is None:
                raise ValueError("Octave version must be MAJOR.MINOR,"
                                 " e.g. 4.4")
            major, minor = match.groups()
            return int(major), int(minor)

    @classmethod
    def get_version(cls, major, minor):
        if major == "latest":
            language = Octave_Latest_Language()
        elif major < 4 or (major == 4 and
                           minor < 2):
            raise ValueError("earliest Octave language supported is 4.2")
        elif major > 7 or (major == 7 and
                           minor > 2):
            raise ValueError("latest Octave language supported is 7.2")
        elif major == 4 and minor < 4:
            language = Octave_4_2_Language()
        else:
            language = Octave_4_4_Language()
        return language


class MATLAB_2017b_Language(Base_MATLAB_Language):
    def __init__(self, name="MATLAB 2017b"):
        super().__init__(name)


class MATLAB_2020b_Language(MATLAB_2017b_Language):
    def __init__(self, name="MATLAB 2020b"):
        super().__init__(name)

        self.hex_literals = True


class MATLAB_2021a_Language(MATLAB_2020b_Language):
    def __init__(self, name="MATLAB 2021a"):
        super().__init__(name)

        self.string_argument_pairs = True


class MATLAB_Latest_Language(MATLAB_2021a_Language):
    pass


class Octave_4_2_Language(Base_Octave_Language):
    def __init__(self, name = "Octave 4.2"):
        super().__init__(name)


class Octave_4_4_Language(Octave_4_2_Language):
    def __init__(self, name = "Octave 4.4"):
        super().__init__(name)

        self.allow_classdef_subfunctions = True


class Octave_Latest_Language(Octave_4_4_Language):
    pass
