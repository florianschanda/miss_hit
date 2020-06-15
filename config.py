#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2020,      Florian Schanda                    ##
##              Copyright (C) 2019-2020, Zenuity AB                         ##
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

DEFAULT_NAMING_SCHEME = "([A-Z]+|[A-Z][a-z]*)(_([A-Z]+|[A-Z][a-z]*|[0-9]+))*"
# Underscore-separated acronyms or capitalised words. For example
# "Kitten_Class" or "LASER", but not "potatoFarmer".

BASE_CONFIG = {
    "enable"                     : True,
    "octave"                     : False,
    "ignore_pragmas"             : False,
    "copyright_entity"           : set(),
    "copyright_in_embedded_code" : False,
    "exclude_dir"                : set(),
    "suppress_rule"              : set(),
    "regex_class_name"           : DEFAULT_NAMING_SCHEME,
    "regex_function_name"        : DEFAULT_NAMING_SCHEME,
    "regex_nested_name"          : DEFAULT_NAMING_SCHEME,
    "regex_method_name"          : "[a-z]+(_[a-z]+)*",
    "file_length"                : 1000,
    "line_length"                : 80,
    "tab_width"                  : 4,
    "metrics"                    : {}
}

STYLE_RULES = {
    "file_length" : ("Ensures files do not get too big."),
    "line_length" : ("Ensures lines do not get too long."),
    "copyright_notice" : ("Ensures the first thing in each file is a"
                          " copyright notice."),
    "no_starting_newline" : ("Ensures files do not start with newlines."),
    "whitespace_comma" : ("Ensures there is no whitespace before a comma"
                          " and whitespace after."),
    "whitespace_colon" : ("Ensures there is no whitespace around colons"
                          " except if they come after a comma."),
    "whitespace_assignment" : ("Ensures there is whitespace around the"
                               " assignment operator (=)."),
    "whitespace_brackets" : ("Ensures no whitespace after (/[, and no "
                             " whitespace before )/]."),
    "whitespace_keywords" : ("Ensures whitespace after some words, such as "
                             " if, or properties."),
    "whitespace_comments" : ("Ensures whitespace before comments and"
                             " whitespace between the % and the body of the"
                             " comment. Pragmas (%#) are exempt."),
    "whitespace_continuation" : ("Ensures whitespace before continuations and"
                                 " whitespace between the ... and any in-line"
                                 " comment."),
    "operator_after_continuation" : ("Complains about operators after"
                                     " a line continuation."),
    "dangerous_continuation": ("Flag misleading line continuations."),
    "useless_continuation" : ("Flag unnecessary line continuations."),
    "operator_whitespace" : ("Enfore whitespace around unary and binary"
                             " operators."),
    "end_of_statements" : ("Ensures consistent ending of statements."),
    "builtin_shadow" : ("Checks that assignments do not overwrite builtin"
                        " functions such as true, false, or pi."),
    "naming_functions" : ("Checks names of functions, nested functions, and"
                          " class methods."),
    "naming_classes" : ("Checks names of classes."),
    "indentation" : ("Make indentation consistent."),
    "redundant_brackets" : ("Check for obviously useless brackets. Does not"
                            " complain about brackets added for clarity."),
    "annotation_whitespace": ("Check for a space after %|"),
    "implicit_shortcircuit": ("Complain about implicit short-circuit"
                              " operations in if or while guards"),
}

METRICS = {
    "file_length" : {
        "kind" : "file",
        "type" : "int",
        "help" : "Number of lines in each file.",
        "name" : "File lines",
    },
    "function_length" : {
        "kind" : "function",
        "type" : "int",
        "help" : "Number for lines for each function.",
        "name" : "Function lines",
    },
    "npath" : {
        "kind" : "function",
        "type" : "int",
        "help" : ("Approximation for maximum number of paths in"
                  " function."),
        "name" : "Number of paths",
    },
    "cnest" : {
        "kind" : "function",
        "type" : "int",
        "help" : "Maximum nesting of control structures.",
        "name" : "Control nesting",
    },
    "parameters" : {
        "kind" : "function",
        "type" : "int",
        "help" : "Number of input/output parameters.",
        "name" : "Parameters",
    },
    "globals" : {
        "kind" : "function",
        "type" : "int",
        "help" : "Number of direct (non-transitive) global variables.",
        "name" : "Globals",
    },
    "persistent" : {
        "kind" : "function",
        "type" : "int",
        "help" : "Number of persistent variables.",
        "name" : "Persistents",
    },
    "cyc" : {
        "kind" : "function",
        "type" : "int",
        "help" : "The McCabe cyclomatic complexity metric.",
        "name" : "Cyclomatic complexity",
    },
}
FILE_METRICS = sorted(metric
                      for metric in METRICS
                      if METRICS[metric]["kind"] == "file")
FUNCTION_METRICS = sorted(metric
                          for metric in METRICS
                          if METRICS[metric]["kind"] == "function")


def active(cfg, rule):
    assert isinstance(cfg, dict)
    assert isinstance(rule, str)
    assert rule in STYLE_RULES
    return rule not in cfg["suppress_rule"]


def metric_enabled(cfg, metric):
    """ Returns true if the given metric should be collected. """
    assert isinstance(cfg, dict)
    assert isinstance(metric, str)
    assert metric in METRICS

    if metric not in cfg["metrics"]:
        return True

    return not cfg["metrics"][metric].get("disable", False)


def metric_check(cfg, metric):
    """ Returns true if the given metric should be checked
        against some limit.
    """
    assert isinstance(cfg, dict)
    assert isinstance(metric, str)
    assert metric in METRICS

    if metric not in cfg["metrics"]:
        return False

    return "max" in cfg["metrics"][metric]


def metric_upper_limit(cfg, metric):
    assert isinstance(cfg, dict)
    assert isinstance(metric, str)
    assert metric in METRICS
    assert METRICS[metric]["type"] == "int"

    if metric in cfg["metrics"]:
        return cfg["metrics"][metric]["max"]
    else:
        return None
