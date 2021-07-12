#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2020-2021, Florian Schanda                    ##
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

from copy import deepcopy


##############################################################################
# Configuration class. This will be passed to every bit of code that
# analyzes anything.
##############################################################################

class Config:
    def __init__(self, other=None):
        if other is None:
            # Set up default configuration

            self.enabled = True
            self.octave  = False
            self.pragmas = True
            # MH is enabled, octave mode is off, and we process pragmas

            self.style_rules = set(STYLE_RULES)
            # All rules are enabled

            self.style_config = {
                cfg_name: deepcopy(STYLE_CONFIGURATION[cfg_name].default)
                for cfg_name in STYLE_CONFIGURATION
            }
            # All rule configuration is default

            self.enabled_metrics = set(METRICS)
            # All metrics are enabled

            self.metric_limits = {}
            # No metrics have configured limits

        else:
            assert isinstance(other, Config)
            # Inherit from existing configuration
            self.enabled         = other.enabled
            self.octave          = other.octave
            self.pragmas         = other.pragmas
            self.style_rules     = deepcopy(other.style_rules)
            self.style_config    = deepcopy(other.style_config)
            self.enabled_metrics = deepcopy(other.enabled_metrics)
            self.metric_limits   = deepcopy(other.metric_limits)

    def dump(self, indent=0):
        items = ["MH Configuration object"]
        items.append("Enabled = %s" % self.enabled)
        items.append("Octave  = %s" % self.octave)
        items.append("Pragmas = %s" % self.pragmas)
        items.append("Style Rules")
        maxlen = max(len(item) for item in STYLE_RULES)
        for rule in sorted(STYLE_RULES):
            items.append("  %-*s = %s" % (maxlen,
                                          rule,
                                          rule in self.style_rules))
        items.append("Style Configuration")
        maxlen = max(len(item) for item in STYLE_CONFIGURATION)
        for config in sorted(STYLE_CONFIGURATION):
            items.append("  %-*s = %s" % (maxlen,
                                          config,
                                          self.style_config[config]))
        items.append("Metrics")
        maxlen = max(len(item) for item in METRICS)
        for metric in sorted(METRICS):
            if metric in self.metric_limits:
                assert metric in self.enabled_metrics
                items.append("  %-*s = limit %u" %
                             (maxlen,
                              metric,
                              self.metric_limits[metric]))
            else:
                items.append(
                    "  %-*s = %s" %
                    (maxlen,
                     metric,
                     {False: "ignore",
                      True: "report"}[metric in self.enabled_metrics]))

        for i, item in enumerate(items):
            if i == 0:
                print("%s%s" % (" " * indent, item))
            else:
                print("%s| %s" % (" " * indent, item))

    def active(self, rule):
        """ Returns true if the given rule is active. """
        assert isinstance(rule, str)
        assert rule in STYLE_RULES

        return rule in self.style_rules

    def metric_enabled(self, metric):
        """ Returns true if the given metric should be collected. """
        assert isinstance(metric, str)
        assert metric in METRICS

        return metric in self.enabled_metrics

    def metric_check(self, metric):
        """ Returns true if the given metric should be checked
            against some limit.
        """
        assert isinstance(metric, str)
        assert metric in METRICS

        return metric in self.metric_limits

    def metric_upper_limit(self, metric):
        assert isinstance(metric, str)
        assert metric in METRICS

        return self.metric_limits.get(metric, None)


##############################################################################
# Internal classes describing the kind of configuration you can put in
# a config file.
##############################################################################

class Style_Configuration:
    def __init__(self, description, default=None):
        assert isinstance(description, str)
        self.description = description
        self.default     = default


class Boolean_Style_Configuration(Style_Configuration):
    pass


class Integer_Style_Configuration(Style_Configuration):
    def __init__(self, description,
                 lower_limit=None, upper_limit=None, default=None):
        super().__init__(description, default)
        assert isinstance(lower_limit, int) or lower_limit is None
        assert isinstance(upper_limit, int) or upper_limit is None
        assert isinstance(default, int) or default is None
        assert lower_limit is None or upper_limit is None or \
            lower_limit <= upper_limit
        assert lower_limit is None or default is None or default >= lower_limit
        assert upper_limit is None or default is None or default <= upper_limit

        self.lower_limit = lower_limit
        self.upper_limit = upper_limit


class String_Style_Configuration(Style_Configuration):
    def __init__(self, description, default=None):
        assert isinstance(default, str) or default is None
        super().__init__(description, default)


class Choice_Style_Configuration(String_Style_Configuration):
    def __init__(self, description, choices):
        assert isinstance(choices, list)
        assert len(choices) >= 1
        for choice in choices:
            assert isinstance(choice, str)
        super().__init__(description, choices[0])

        self.choices = choices


class Regex_Style_Configuration(String_Style_Configuration):
    pass


class Copyright_Regex_Style_Configuration(Regex_Style_Configuration):
    pass


class Encoding_Style_Configuration(String_Style_Configuration):
    pass


class Set_Style_Configuration(Style_Configuration):
    def __init__(self, description):
        super().__init__(description, set())


class Style_Rule:
    def __init__(self, description, configuration=None):
        assert isinstance(description, str)
        assert configuration is None or \
            isinstance(configuration, dict)

        self.description   = description
        self.configuration = {}

        if configuration:
            for cfg_name in configuration:
                cfg_item = configuration[cfg_name]
                assert isinstance(cfg_name, str)
                assert isinstance(cfg_item, Style_Configuration)
                self.configuration[cfg_name] = cfg_item


class Code_Metric:
    def __init__(self, longname, description):
        assert isinstance(longname, str)
        assert isinstance(description, str)
        self.longname    = longname
        self.description = description


class File_Metric(Code_Metric):
    pass


class Function_Metric(Code_Metric):
    pass


##############################################################################
# The actual configuration options
##############################################################################

DEFAULT_NAMING_SCHEME = "([A-Z]+|[A-Z][a-z]*)(_([A-Z]+|[A-Z][a-z]*|[0-9]+))*"
# Underscore-separated acronyms or capitalised words. For example
# "Kitten_Class" or "LASER", but not "potatoFarmer".

DEFAULT_LC_NAMING_SCHEME = "[a-z]+(_[a-z]+)*"
# A much simpler naming scheme: underscore separated lowercase without
# numbers.

STYLE_RULES = {
    "file_length" : Style_Rule(
        "Ensures files do not get too big.",
        {"file_length": Integer_Style_Configuration(
            "Maximum number of allowed lines.",
            lower_limit = 1,
            default = 1000)}),

    "line_length" : Style_Rule(
        "Ensures lines do not get too long.",
        {"line_length": Integer_Style_Configuration(
            "Maximum allowed characters in any line.",
            lower_limit = 1,
            default = 80)}),

    "copyright_notice" : Style_Rule(
        "Ensures the first thing in each file is a copyright notice.",
        {
            "copyright_location": Choice_Style_Configuration(
                "Location of copyright statements",
                ["docstring", "file_header"]),
            "copyright_regex": Copyright_Regex_Style_Configuration(
                ("Regex for picking out copyright notice. Must include "
                 "named groups: 'copy', 'ystart', 'yend', and 'org'"),
                default =
                (r"(?P<copy>(Copyright \([cC]\))|((\([cC]\) )?Copyright)) "
                 r"((?P<ystart>\d\d\d\d)(-| - ))?(?P<yend>\d\d\d\d)"
                 r"( by)? *(?P<org>.*)")),
            "copyright_entity": Set_Style_Configuration(
                "Valid copyright holder."),
            "copyright_primary_entity": String_Style_Configuration(
                "Valid primary copyright holder."),
            "copyright_3rd_party_entity": Set_Style_Configuration(
                "Recognised 3rd-party copyright holder."),
            "copyright_in_embedded_code": Boolean_Style_Configuration(
                ("Enforce copyright statements in code embedded in Simulink"
                 " models."),
                False),
        }),

    "no_starting_newline" : Style_Rule(
        "Ensures files do not start with newlines."),

    "whitespace_comma" : Style_Rule(
        "Ensures there is no whitespace before a comma and whitespace (or a"
        " newline) after."),

    "whitespace_semicolon" : Style_Rule(
        "Ensures there is no whitespace before a semicolon and whitespace"
        " (or a newline) after."),

    "spurious_row_comma" : Style_Rule(
        "Ensures there are no unnecessary leading or trailing commas in a"
        " matrix or cell."),

    "spurious_row_semicolon" : Style_Rule(
        "Ensures there are no unnecessary leading or trailing semicolons in a"
        " matrix or cell."),

    "whitespace_colon" : Style_Rule(
        "Ensures there is no whitespace around colons except if they come"
        " after a comma."),

    "whitespace_assignment" : Style_Rule(
        "Ensures there is whitespace around the assignment operator (=)."),

    "whitespace_brackets" : Style_Rule(
        "Ensures no whitespace after (/[, and no whitespace before )/]."),

    "whitespace_keywords" : Style_Rule(
        "Ensures whitespace after some words, such as if, or properties."),

    "whitespace_comments" : Style_Rule(
        "Ensures whitespace before comments and whitespace between the % and"
        " the body of the comment. Pragmas (%#) are exempt."),

    "whitespace_continuation" : Style_Rule(
        "Ensures whitespace before continuations and whitespace between"
        " the ... and any in-line comment."),

    "whitespace_around_functions" : Style_Rule(
        "Ensures there is whitespace around functions."),

    "operator_after_continuation" : Style_Rule(
        "Complains about operators after a line continuation."),

    "dangerous_continuation": Style_Rule(
        "Flag misleading line continuations."),

    "useless_continuation" : Style_Rule(
        "Flag unnecessary line continuations."),

    "operator_whitespace" : Style_Rule(
        "Enfore whitespace around unary and binary operators."),

    "end_of_statements" : Style_Rule(
        "Ensures consistent ending of statements."),

    "builtin_shadow" : Style_Rule(
        "Checks that assignments do not overwrite builtin functions such as"
        " true, false, or pi."),

    "naming_scripts" : Style_Rule(
        "Checks names of script files.",
        {
            "regex_script_name" : Regex_Style_Configuration(
                "Regex for script names",
                default = DEFAULT_NAMING_SCHEME),
        }),

    "naming_functions" : Style_Rule(
        "Checks names of functions, nested functions, and class methods.",
        {
            "regex_function_name" : Regex_Style_Configuration(
                "Regex for function names",
                default = DEFAULT_NAMING_SCHEME),
            "regex_nested_name" : Regex_Style_Configuration(
                "Regex for nested function names",
                default = DEFAULT_NAMING_SCHEME),
            "regex_method_name" : Regex_Style_Configuration(
                "Regex for class method names",
                default = DEFAULT_LC_NAMING_SCHEME)
        }),

    "naming_parameters" : Style_Rule(
        "Checks names of function and method parameters.",
        {
            "regex_parameter_name" : Regex_Style_Configuration(
                "Regex for parameter names",
                default = DEFAULT_LC_NAMING_SCHEME)
        }),

    "naming_classes" : Style_Rule(
        "Checks names of classes.",
        {
            "regex_class_name" : Regex_Style_Configuration(
                "Regex for class names",
                default = DEFAULT_NAMING_SCHEME)
        }),

    "naming_enumerations" : Style_Rule(
        "Checks names of enumerations.",
        {
            "regex_enumeration_name" : Regex_Style_Configuration(
                "Regex for parameter names",
                default = DEFAULT_NAMING_SCHEME)
        }),

    "indentation" : Style_Rule(
        "Make indentation consistent.",
        {
            "tab_width": Integer_Style_Configuration(
                "Number of spaces to indent by.",
                lower_limit = 2,
                default = 4),
            "align_round_brackets" : Boolean_Style_Configuration(
                "Align continuations inside normal brackets.",
                default = True),
            "align_other_brackets" : Boolean_Style_Configuration(
                "Align continuations inside matrix and cell expressions.",
                default = True)
        }),

    "redundant_brackets" : Style_Rule(
        "Check for obviously useless brackets. Does not complain about"
        " brackets added for clarifying operator precedence."),

    "annotation_whitespace" : Style_Rule("Check for a space after %|"),

    "implicit_shortcircuit": Style_Rule(
        "Complain about implicit short-circuit operations in"
        " if or while guards"),

    "unicode": Style_Rule(
        "Complain about non-conforming characters in source files",
        {
            "enforce_encoding": Encoding_Style_Configuration(
                "Override the encoding to enforence, by default ASCII",
                default = "ascii"),
            "enforce_encoding_comments" : Boolean_Style_Configuration(
                ("Also check comments/continuations for conforming to "
                 "the encoding"),
                default = True)
        }),
}

STYLE_CONFIGURATION = {
    cfg_name: STYLE_RULES[rule_name].configuration[cfg_name]
    for rule_name in STYLE_RULES
    for cfg_name in STYLE_RULES[rule_name].configuration
}
# A flat list of all style configuration items

STYLE_CONFIGURATION["regex_tickets"] = Regex_Style_Configuration(
    "Regex for tickets in your issue tracking system",
    default = "")
# Add the special regex that identifies tickets (not part of any
# rule).

METRICS = {
    "file_length" : File_Metric(
        "File lines",
        "Number of lines in each file."),

    "function_length" : Function_Metric(
        "Function lines",
        "Number for lines for each function."),

    "npath" : Function_Metric(
        "Number of paths",
        "Approximation for maximum number of paths in function."),

    "cnest" : Function_Metric(
        "Control nesting",
        "Maximum nesting of control structures."),

    "parameters" : Function_Metric(
        "Parameters",
        "Number of input/output parameters."),

    "globals" : Function_Metric(
        "Globals",
        "Number of direct (non-transitive) global variables."),

    "persistent" : Function_Metric(
        "Persistents",
        "Number of persistent variables."),

    "cyc" : Function_Metric(
        "Cyclomatic complexity",
        "The McCabe cyclomatic complexity metric."),
}
FILE_METRICS = sorted(metric
                      for metric in METRICS
                      if isinstance(METRICS[metric], File_Metric))
FUNCTION_METRICS = sorted(metric
                          for metric in METRICS
                          if isinstance(METRICS[metric], Function_Metric))
assert len(FILE_METRICS) + len(FUNCTION_METRICS) == len(METRICS)
