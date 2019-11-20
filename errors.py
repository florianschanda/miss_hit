#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2019, Florian Schanda                         ##
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

import sys


class Location:
    """ This fully describes where a message originates from """
    def __init__(self,
                 filename,
                 line=None,
                 col_start=None,
                 col_end=None,
                 context=None):
        assert isinstance(filename, str)
        assert line is None or (isinstance(line, int) and line >= 1)
        assert col_start is None or (isinstance(col_start, int) and
                                     col_start >= 0)
        assert col_end is None or (isinstance(col_end, int) and
                                   col_end >= 0 and
                                   col_start is not None)
        assert context is None or isinstance(context, str)

        self.filename = filename
        self.line     = line
        self.col_start = col_start
        if col_end is None:
            self.col_end = col_start
        else:
            self.col_end = max(col_start, col_end)
        self.context = context

    def __lt__(self, other):
        assert isinstance(other, Location)

        return (self.filename, self.line, self.col_start) < \
            (other.filename, other.line, other.col_start)

class ICE(Exception):
    """ Internal compiler errors """
    def __init__(self, reason):
        self.reason = reason


class Error(Exception):
    """ Any other, possibly recoverable, errors """
    def __init__(self, location, message):
        assert isinstance(location, Location)
        assert isinstance(message, str)

        self.location = location
        self.message = message


class Message_Handler:
    """ All messages should be routed through this class """
    def __init__(self):
        self.warnings = 0
        self.style_issues = 0
        self.errors = 0
        self.files = set()

        self.show_context = True
        self.sort_messages = True
        self.messages = []

    def register_file(self, filename):
        assert isinstance(filename, str)
        assert filename not in self.files

        self.files.add(filename)

    def __render_message(self, location, kind, message):
        if location.line is None:
            print("%s: %s: %s" % (location.filename,
                                  kind,
                                  message))
        elif location.col_start is None:
            print("%s:%u: %s: %s" % (location.filename,
                                     location.line,
                                     kind,
                                     message))
        else:
            if location.context is None:
                show_context = False
            elif len(location.context.strip()) > 0:
                show_context = self.show_context
            else:
                show_context = False
            if show_context:
                print("In %s, line %u" % (location.filename, location.line))
                print("| " + location.context.replace("\t", " "))
                print("| " +
                      (" " * location.col_start) +
                      ("^" * (location.col_end - location.col_start + 1)) +
                      " %s: %s" % (kind, message))
            else:
                print("%s:%u:%u: %s: %s" % (location.filename,
                                            location.line,
                                            location.col_start,
                                            kind,
                                            message))

    def __register_message(self, location, kind, message):
        assert isinstance(location, Location)
        assert kind in ("info", "style", "warning", "lex error", "error")
        assert isinstance(message, str)

        if location.filename not in self.files:
            raise ICE("attempted to emit message on unknown file")

        # TODO: Use bisect to keep it sorted
        if self.sort_messages:
            self.messages.append((location, kind, message))
        else:
            self.__render_message(location, kind, message)

        if kind == "info":
            pass
        elif kind == "style":
            self.style_issues += 1
        elif kind == "warning":
            self.warnings += 1
        else:
            self.errors += 1
            raise Error(location, message)

    def info(self, location, message):
        self.__register_message(location, "info", message)

    def style_issue(self, location, message):
        self.__register_message(location, "style", message)

    def warning(self, location, message):
        self.__register_message(location, "warning", message)

    def lex_error(self, location, message):
        self.__register_message(location, "lex error", message)

    def error(self, location, message):
        self.__register_message(location, "error", message)

    def print_summary_and_exit(self):
        for location, kind, message in sorted(self.messages):
            self.__render_message(location, kind, message)

        tmp = "MISS_HIT Summary: "
        stats = ["%u file(s) analysed" % len(self.files)]
        if self.style_issues:
            stats.append("%u style issue(s)" % self.style_issues)
        if self.warnings:
            stats.append("%u warning(s)" % self.warnings)
        if self.errors:
            stats.append("%u error(s)" % self.errors)
        if len(stats) == 1:
            stats.append("everything semes fine")
        tmp += ", ".join(stats)
        print(tmp)

        if self.style_issues or self.warnings or self.errors:
            sys.exit(1)
        else:
            sys.exit(0)


mh = Message_Handler()
