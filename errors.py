#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2019, Florian Schanda                         ##
##              Copyright (C) 2019, Zenuity AB                              ##
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

        return (self.filename,
                self.line if self.line else 0,
                self.col_start if self.col_start else -1) < \
            (other.filename,
             other.line if other.line else 0,
             other.col_start if other.col_start else -1)


class ICE(Exception):
    """ Internal compiler errors """
    def __init__(self, reason):
        super().__init__()
        self.reason = reason


class Error(Exception):
    """ Any other, possibly recoverable, errors """
    def __init__(self, location, message):
        assert isinstance(location, Location)
        assert isinstance(message, str)

        super().__init__()
        self.location = location
        self.message = message


class Justification:
    def __init__(self, token):
        # assert isinstance(token, m_lexer.MATLAB_Token)
        assert token.kind in ("COMMENT", "CONTINUATION")

        self.token = token
        self.used = False


class Style_Justification(Justification):
    pass


class Message_Handler:
    """ All messages should be routed through this class """
    def __init__(self):
        self.warnings = 0
        self.style_issues = 0
        self.errors = 0
        self.justified = 0
        self.files = set()
        self.excluded_files = set()

        self.autofix = False
        self.colour = False
        self.show_context = True
        self.show_style = True
        self.sort_messages = True
        self.messages = []
        self.html = False

        self.style_justifications = {}

    def register_file(self, filename):
        assert isinstance(filename, str)
        assert filename not in self.files
        assert filename not in self.excluded_files

        self.files.add(filename)
        self.style_justifications[filename] = {}

    def register_exclusion(self, filename):
        assert isinstance(filename, str)
        assert filename not in self.files
        assert filename not in self.excluded_files

        self.excluded_files.add(filename)

    def unregister_file(self, filename):
        assert isinstance(filename, str)
        assert filename in self.files

        self.files.remove(filename)
        del self.style_justifications[filename]

        self.messages = [m
                         for m in self.messages
                         if m.location.filename != filename]

    def __render_message(self, location, kind, message, autofix):
        # First, check if a justification applies
        if kind == "style":
            st_just = self.style_justifications[location.filename]
            if location.line in st_just:
                st_just[location.line].used = True
                self.justified += 1
                return

            if not self.show_style:
                return

        # Count the message. Note that errors have already been
        # counted, so don't count them again,
        if kind == "info":
            pass
        elif kind == "style":
            self.style_issues += 1
        elif kind == "warning":
            self.warnings += 1

        if self.colour:
            if kind in ("error", "lex error"):
                kstring = "\033[31;1m%s\033[0m" % kind
            elif kind == "warning":
                kstring = "\033[31m%s\033[0m" % kind
            else:
                kstring = kind
        else:
            kstring = kind

        if autofix and self.autofix:
            message += " [fixed]"

        if location.line is None:
            print("%s: %s: %s" % (location.filename,
                                  kstring,
                                  message))
        elif location.col_start is None:
            print("%s:%u: %s: %s" % (location.filename,
                                     location.line,
                                     kstring,
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
                      " %s: %s" % (kstring, message))
            else:
                print("%s:%u:%u: %s: %s" % (location.filename,
                                            location.line,
                                            location.col_start,
                                            kstring,
                                            message))

    def __render_message_as_html(self, location, kind, message, autofix):
        if not autofix:
            tmp = ("<a href=\"matlab:opentoline('%s', %u, %u)\">" %
                   (location.filename, location.line, location.col_start + 1))
            tmp += "<div class=\"file_mention\">"
            tmp += "%s at %u: <code>%s: %s</code>" % (location.filename,
                                                      location.line,
                                                      kind,
                                                      message)
            tmp += "</div></a>\n"
            return tmp
        else:
            return ""

    def __register_message(self, location, kind, message, fatal, autofix):
        assert isinstance(location, Location)
        assert kind in ("info", "style", "warning", "lex error", "error")
        assert isinstance(message, str)
        assert isinstance(fatal, bool)
        assert isinstance(autofix, bool)

        if location.filename not in self.files:
            raise ICE("attempted to emit message on unknown file")

        # TODO: Use bisect to keep it sorted
        if self.sort_messages:
            self.messages.append((location, kind, message, autofix))
        else:
            self.__render_message(location, kind, message, autofix)

        if kind in ("lex error", "error"):
            self.errors += 1

        if fatal:
            raise Error(location, message)

    def register_justification(self, token):
        # assert isinstance(token, m_lexer.MATLAB_Token)
        assert token.kind in ("COMMENT", "CONTINUATION")

        if "mh:ignore_style" in token.value():
            just = Style_Justification(token)
            st_just = self.style_justifications[token.location.filename]
            st_just[token.location.line] = just
        else:
            self.warning(token.location,
                         "invalid justification not recognized")

    def info(self, location, message):
        self.__register_message(location, "info", message, False, False)

    def style_issue(self, location, message, autofix=False):
        self.__register_message(location, "style", message, False, autofix)

    def warning(self, location, message):
        self.__register_message(location, "warning", message, False, False)

    def lex_error(self, location, message, fatal=True):
        self.__register_message(location, "lex error", message, fatal, False)

    def error(self, location, message, fatal=True):
        self.__register_message(location, "error", message, fatal, False)

    def flush_messages(self, filename):
        assert isinstance(filename, str)
        assert filename in self.files

        # Keep all messages for the HTML report
        if self.html:
            return

        # Check which justifications actually apply here
        for location, kind, message, autofix in self.messages:
            if location.filename != filename:
                continue

            if kind == "style":
                st_just = self.style_justifications[location.filename]
                if location.line in st_just:
                    st_just[location.line].used = True

        # New messages for justifications that did not apply
        for just in self.style_justifications[filename].values():
            if not just.used:
                mh.warning(just.token.location,
                           "style justification does not apply")

        # Sort messages into stuff that applies to us and others
        applicable_msg = []
        other_msg = []
        for location, kind, message, autofix in self.messages:
            if location.filename == filename:
                applicable_msg.append((location, kind, message, autofix))
            else:
                other_msg.append((location, kind, message, autofix))
        self.messages = other_msg

        # Print messages for this file
        for location, kind, message, autofix in sorted(applicable_msg):
            self.__render_message(location, kind, message, autofix)

        # Clean up justifications
        self.style_justifications[filename] = {}

    def print_summary_and_exit(self):
        # Check which justifications actually apply
        for location, kind, message, autofix in sorted(self.messages):
            if kind == "style":
                st_just = self.style_justifications[location.filename]
                if location.line in st_just:
                    st_just[location.line].used = True

        # New messages for justifications that did not apply
        for filename in self.style_justifications:
            for just in self.style_justifications[filename].values():
                if not just.used:
                    mh.warning(just.token.location,
                               "style justification does not apply")

        # Finally print remaining messages
        for location, kind, message, autofix, in sorted(self.messages):
            self.__render_message(location, kind, message, autofix)

        tmp = "MISS_HIT Summary: "
        stats = ["%u file(s) analysed" % len(self.files)]
        if self.style_issues:
            stats.append("%u style issue(s)" % self.style_issues)
        if self.warnings:
            stats.append("%u warning(s)" % self.warnings)
        if self.errors:
            stats.append("%u error(s)" % self.errors)
        if len(stats) == 1:
            stats.append("everything seemes fine")
        if self.justified > 0:
            stats.append("%u justified message(s)" % self.justified)
        tmp += ", ".join(stats)
        if self.excluded_files:
            tmp += ("; %u file(s) excluded from analysis" %
                    len(self.excluded_files))
        print(tmp)

        if self.style_issues or self.warnings or self.errors:
            sys.exit(1)
        else:
            sys.exit(0)

    def print_html_and_exit(self, html_file):
        with open(html_file, "w") as fd:
            fd.write("<html>\n")
            fd.write("<head>\n")
            fd.write("<link type=\"text/css\" rel=\"stylesheet\" "
                     "href=\"html/style.css\">\n")
            fd.write("</head>\n")
            fd.write("<body>\n")
            for location, kind, message, autofix in sorted(self.messages):
                fd.write(self.__render_message_as_html(location,
                                                       kind,
                                                       message,
                                                       autofix))
            fd.write("</body>\n")
            fd.write("</html>\n")

        if self.style_issues or self.warnings or self.errors:
            sys.exit(1)
        else:
            sys.exit(0)


# pylint: disable=invalid-name
mh = Message_Handler()
# pylint: enable=invalid-name
