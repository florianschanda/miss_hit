#!/usr/bin/env python3
##############################################################################
##                                                                          ##
##          MATLAB Independent, Small & Safe, High Integrity Tools          ##
##                                                                          ##
##              Copyright (C) 2019-2021, Florian Schanda                    ##
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

import os
import sys
import html
import json


class Location:
    """ This fully describes where a message originates from.

    * filename must be an actual file where the message is attached
    * blockname can describe a virtual construct (e.g. simulink block)
    * line is the line number (starts at 1)
    * col_start and col_end describe the column (starts at 0)
    * context is a replication of the line that contains the offending
      construct
    """
    def __init__(self,
                 filename,
                 line=None,
                 col_start=None,
                 col_end=None,
                 context=None,
                 blockname=None):
        assert isinstance(filename, str)
        assert blockname is None or isinstance(blockname, str)
        assert line is None or (isinstance(line, int) and line >= 1)
        assert col_start is None or (isinstance(col_start, int) and
                                     col_start >= 0)
        assert col_end is None or (isinstance(col_end, int) and
                                   col_end >= 0 and
                                   col_start is not None)
        assert context is None or isinstance(context, str)

        self.filename = filename.replace("\\", "/")
        # We canonicalise filenames so that windows and linux produce
        # the same output.

        self.blockname = blockname

        self.line = line
        self.col_start = col_start
        if col_end is None:
            self.col_end = col_start
        else:
            self.col_end = max(col_start, col_end)
        self.context = context

    def __str__(self):
        return "Location(%s,l=%s,b=%s)" % (self.filename,
                                           self.line,
                                           self.blockname)

    def __lt__(self, other):
        assert isinstance(other, Location)

        return (self.filename,
                self.line if self.line else 0,
                self.col_start if self.col_start else -1) < \
            (other.filename,
             other.line if other.line else 0,
             other.col_start if other.col_start else -1)

    def to_json(self, detailed=True):
        rv = {"filename": self.filename}
        if self.blockname:
            rv["block"] = self.blockname
        if self.line:
            rv["line"] = self.line
        if self.col_start:
            rv["col_start"] = self.col_start
        if detailed and self.col_end:
            rv["col_end"] = self.col_end
        if detailed and self.context:
            rv["context"] = self.context
        return rv

    def short_string(self):
        rv = self.filename
        if self.line:
            rv += ":%u" % self.line
        return rv


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


class Message:
    def __init__(self, location, kind, message, fatal, autofixed):
        assert isinstance(location, Location)
        assert kind in ("info",       # diagnostics and information
                        "style",      # style issues (from mh_style)
                        "metric",     # code metrics (from mh_metric)
                        "check",      # defects (from mh_lint and mh_prove)
                        "warning",    # other issues
                        "lex error",  # errors in the lexing phase
                        "error")      # other errors
        assert isinstance(message, str)
        assert isinstance(fatal, bool)
        assert isinstance(autofixed, bool)
        assert not fatal or kind in ("lex error", "error"), \
            "fatal=%s, kind=%s violates precondition" % (fatal, kind)

        self.location  = location
        self.kind      = kind
        self.severity  = "medium"  # can be low, medium, high
        self.message   = message
        self.fixed     = autofixed
        self.fatal     = fatal
        self.justified = False

    def __str__(self):
        return "Message(%s,%s,%s)" % (self.location,
                                      self.kind,
                                      repr(self.message))

    def __lt__(self, other):
        assert isinstance(other, Message)

        return self.location < other.location

    def check_justification(self, justification):
        if self.kind == "style" and \
           isinstance(justification, Style_Justification):
            if self.location.line == justification.token.location.line:
                self.justified = True
                justification.used = True

    def to_json(self):
        return {"location"  : self.location.to_json(),
                "kind"      : self.kind,
                "severity"  : self.severity,
                "message"   : self.message,
                "fixable"   : self.fixed,
                "fatal"     : self.fatal}


class Check_Message(Message):
    def __init__(self, location, severity, message):
        super().__init__(location  = location,
                         kind      = "check",
                         message   = message,
                         fatal     = False,
                         autofixed = False)
        assert severity in ("low", "medium", "high")
        self.severity = severity


class Message_Handler:
    """ All messages should be routed through this class """
    def __init__(self, tool_id):
        assert tool_id in ("debug",
                           "style", "metric",
                           "lint", "trace", "bmc",
                           "diff", "copyright")

        self.tool_id = tool_id

        self.style_issues = 0
        self.metric_issues = 0
        self.metric_justifications = 0
        self.checks = 0
        self.warnings = 0
        self.errors = 0
        self.justified = 0
        self.files = set()
        self.excluded_files = set()
        self.seen_files = set()

        self.autofix = False
        self.colour = False
        self.show_context = True
        self.show_style = True
        self.show_checks = False
        self.sort_messages = True

        self.messages = {}        # file -> line -> [message]
        self.justifications = {}  # file -> line -> [justification]

    def debug_dump(self):
        print("Debug dump for Message_Handler object")
        for file_name in self.messages:
            print("> File name: %s" % file_name)
            for line in sorted(self.messages[file_name]):
                print("  Line: %u" % line)
                for msg in self.messages[file_name][line]:
                    print("    ", str(msg))

    def reset_seen(self):
        self.seen_files = set()

    def fork(self):
        rv = Message_Handler(self.tool_id)
        self.fork_copy_attributes(rv)
        return rv

    def fork_copy_attributes(self, other):
        other.autofix       = self.autofix
        other.colour        = self.colour
        other.show_context  = self.show_context
        other.show_style    = self.show_style
        other.show_checks   = self.show_checks
        other.sort_messages = self.sort_messages

    def integrate(self, other):
        assert isinstance(other, Message_Handler)
        assert self.autofix       == other.autofix
        assert self.colour        == other.colour
        assert self.show_context  == other.show_context
        assert self.show_style    == other.show_style
        assert self.sort_messages == other.sort_messages

        self.style_issues          += other.style_issues
        self.metric_issues         += other.metric_issues
        self.metric_justifications += other.metric_justifications
        self.checks                += other.checks
        self.warnings              += other.warnings
        self.errors                += other.errors
        self.justified             += other.justified
        self.files                 |= other.files
        self.excluded_files        |= other.excluded_files
        self.seen_files            |= other.seen_files

        for filename in other.messages:
            if filename not in self.messages:
                self.messages[filename] = {}
            for line in other.messages[filename]:
                if line not in self.messages[filename]:
                    self.messages[filename][line] = []
                self.messages[filename][line] += \
                  other.messages[filename][line]

        for filename in other.justifications:
            if filename not in self.justifications:
                self.justifications[filename] = {}
            for line in other.justifications[filename]:
                if line not in self.justifications[filename]:
                    self.justifications[filename][line] = []
                self.justifications[filename][line] += \
                  other.justifications[filename][line]

    def register_file(self, filename):
        assert isinstance(filename, str)
        canonical_filename = filename.replace("\\", "/")
        assert canonical_filename not in self.files
        assert canonical_filename not in self.excluded_files

        self.files.add(canonical_filename)
        self.seen_files.add(canonical_filename)
        self.messages[canonical_filename] = {}
        self.justifications[canonical_filename] = {}

    def register_exclusion(self, filename):
        assert isinstance(filename, str)
        canonical_filename = filename.replace("\\", "/")
        assert canonical_filename not in self.files
        assert canonical_filename not in self.excluded_files

        self.excluded_files.add(canonical_filename)

    def unregister_file(self, filename):
        assert isinstance(filename, str)
        canonical_filename = filename.replace("\\", "/")
        assert canonical_filename in self.files

        self.files.remove(canonical_filename)
        del self.messages[canonical_filename]
        del self.justifications[canonical_filename]

    def process_message(self, message):
        # Count the message
        if message.justified:
            self.justified += 1
            return
        elif message.kind == "info":
            pass
        elif message.kind == "style":
            if self.show_style:
                self.style_issues += 1
            else:
                return
        elif message.kind == "metric":
            self.metric_issues += 1
        elif message.kind == "check":
            if self.show_checks:
                self.checks += 1
            else:
                return
        elif message.kind == "warning":
            self.warnings += 1
        elif message.kind in ("lex error", "error"):
            self.errors += 1
        else:
            raise ICE("unexpeced message kind %s" % message.kind)

        # Emit
        self.emit_message(message)

    def emit_message(self, message):
        if self.colour:
            if message.kind in ("error", "lex error"):
                kstring = "\033[31;1m%s\033[0m" % message.kind
            elif message.kind == "warning":
                kstring = "\033[31m%s\033[0m" % message.kind
            elif message.kind == "check":
                if message.severity == "low":
                    kstring = "%s (\033[34m%s\033[0m)" % (message.kind,
                                                          message.severity)
                elif message.severity == "high":
                    kstring = "%s (\033[31;1m%s\033[0m)" % (message.kind,
                                                            message.severity)
                else:
                    kstring = "%s (\033[33m%s\033[0m)" % (message.kind,
                                                          message.severity)
            else:
                kstring = message.kind
        elif message.kind == "check":
            kstring = message.kind + " (" + message.severity + ")"
        else:
            kstring = message.kind

        mtext = message.message

        if message.fixed and self.autofix:
            mtext += " [fixed]"

        if message.location.blockname is None:
            full_location = message.location.filename
        else:
            full_location = "%s/%s" % (message.location.filename,
                                       message.location.blockname)

        if message.location.line is None:
            print("%s: %s: %s" % (full_location,
                                  kstring,
                                  mtext))
        elif message.location.col_start is None:
            print("%s:%u: %s: %s" % (full_location,
                                     message.location.line,
                                     kstring,
                                     mtext))
        else:
            if message.location.context is None:
                show_context = False
            elif len(message.location.context.strip()) > 0:
                show_context = self.show_context
            else:
                show_context = False

            if show_context:
                print("In %s, line %u" % (full_location,
                                          message.location.line))
                print("| " + message.location.context.replace("\t", " "))
                print("| " +
                      (" " * message.location.col_start) +
                      ("^" * (message.location.col_end -
                              message.location.col_start + 1)) +
                      " %s: %s" % (kstring, mtext))
            else:
                print("%s:%u:%u: %s: %s" % (full_location,
                                            message.location.line,
                                            message.location.col_start,
                                            kstring,
                                            mtext))

    def emit_summary(self):
        tmp = "MISS_HIT %s Summary: " % self.tool_id.capitalize()
        stats = ["%u file(s) analysed" % len(self.seen_files)]
        if self.style_issues:
            stats.append("%u style issue(s)" % self.style_issues)
        if self.metric_issues:
            stats.append("%u metric deviations(s)" % self.metric_issues)
        if self.checks:
            stats.append("%u check(s)" % self.checks)
        if self.warnings:
            stats.append("%u warning(s)" % self.warnings)
        if self.errors:
            stats.append("%u error(s)" % self.errors)
        if len(stats) == 1:
            stats.append("everything seems fine")
        if self.justified > 0:
            stats.append("%u justified message(s)" % self.justified)
        if self.metric_justifications > 0:
            stats.append("%u justified metric deviations(s)" %
                         self.metric_justifications)
        tmp += ", ".join(stats)
        if self.excluded_files:
            tmp += ("; %u file(s) excluded from analysis" %
                    len(self.excluded_files))
        print(tmp)

    def register_message(self, msg):
        assert isinstance(msg, Message)

        if msg.location.filename not in self.files:
            raise ICE("attempted to emit message on unknown file '%s'" %
                      msg.location.filename)

        if self.sort_messages:
            # Add message to list
            messages = self.messages[msg.location.filename]
            if msg.location.line not in messages:
                messages[msg.location.line] = [msg]
            else:
                messages[msg.location.line].append(msg)

            # Check if a justification applies
            just = self.messages[msg.location.filename]
            if msg.location.line in just:
                for j in just[msg.location.line]:
                    msg.check_justification(j)

        else:
            # Otherwise just immediately emit it
            self.process_message(msg)

        # Raise exception for fatal messages
        if msg.fatal:
            raise Error(msg.location, msg.message)

    def register_justification(self, token):
        # assert isinstance(token, m_lexer.MATLAB_Token)
        assert token.kind in ("COMMENT", "CONTINUATION")

        if token.location.filename not in self.files:
            raise ICE("attempted to add justification to an unknown file")

        if not self.sort_messages:
            return

        if "mh:ignore_style" in token.value:
            justification = Style_Justification(token)
        else:
            self.warning(token.location,
                         "invalid justification not recognized")

        # Add justification
        just = self.justifications[token.location.filename]
        if token.location.line not in just:
            just[token.location.line] = [justification]
        else:
            just[token.location.line].append(justification)

        # Check if a message is justified
        messages = self.messages[token.location.filename]
        if token.location.line in messages:
            for msg in messages[token.location.line]:
                msg.check_justification(justification)

    def info(self, location, message):
        msg = Message(location  = location,
                      kind      = "info",
                      message   = message,
                      fatal     = False,
                      autofixed = False)
        self.register_message(msg)

    def style_issue(self, location, message, autofix=False):
        msg = Message(location  = location,
                      kind      = "style",
                      message   = message,
                      fatal     = False,
                      autofixed = autofix)
        self.register_message(msg)

    def metric_issue(self, location, message):
        msg = Message(location  = location,
                      kind      = "metric",
                      message   = message,
                      fatal     = False,
                      autofixed = False)
        self.register_message(msg)

    def check(self, location, message, severity="medium"):
        msg = Check_Message(location = location,
                            severity = severity,
                            message  = message)
        self.register_message(msg)

    def warning(self, location, message):
        msg = Message(location  = location,
                      kind      = "warning",
                      message   = message,
                      fatal     = False,
                      autofixed = False)
        self.register_message(msg)

    def lex_error(self, location, message, fatal=True):
        msg = Message(location  = location,
                      kind      = "lex error",
                      message   = message,
                      fatal     = fatal,
                      autofixed = False)
        self.register_message(msg)

    def error(self, location, message, fatal=True):
        msg = Message(location  = location,
                      kind      = "error",
                      message   = message,
                      fatal     = fatal,
                      autofixed = False)
        self.register_message(msg)

    def config_error(self, location, message):
        # This is for raising errors in config files _only_.
        canonical_filename = location.filename.replace("\\", "/")
        if canonical_filename not in self.files:
            self.register_file(location.filename)
        self.error(location, message)

    def finalize_file(self, filename):
        assert isinstance(filename, str)
        canonical_filename = filename.replace("\\", "/")
        assert canonical_filename in self.files

        # New messages for justifications that did not apply
        for justifications in self.justifications[canonical_filename].values():
            for justification in justifications:
                if not justification.used:
                    self.warning(justification.token.location,
                                 "style justification does not apply")

        # Process messages
        for messages in sorted(self.messages[canonical_filename].values()):
            for message in sorted(messages):
                self.process_message(message)

        # Remove file
        self.unregister_file(canonical_filename)

    def command_line_error(self, message):
        print("%s: error: %s" % (os.path.basename(sys.argv[0]), message))
        sys.exit(1)

    def summary_and_exit(self):
        files = list(self.messages)
        for filename in files:
            self.finalize_file(filename)

        self.emit_summary()

        if self.style_issues or \
           self.metric_issues or \
           self.warnings or \
           self.errors:
            sys.exit(1)
        else:
            sys.exit(0)


class File_Based_Message_Handler(Message_Handler):
    def __init__(self, tool_id, filename):
        super().__init__(tool_id)
        self.filename = filename
        self.fd       = None

    def fork(self):
        raise ICE("unimplemented abstract class")

    def setup_fd(self):
        raise ICE("unimplemented abstract class")


class HTML_Message_Handler(File_Based_Message_Handler):
    def __init__(self, tool_id, filename):
        super().__init__(tool_id, filename)
        self.last_file = None

    def fork(self):
        rv = HTML_Message_Handler(self.tool_id, self.filename)
        self.fork_copy_attributes(rv)
        return rv

    def setup_fd(self):
        if self.fd is not None:
            return

        self.fd = open(self.filename, "w")
        self.fd.write("<!DOCTYPE html>\n")
        self.fd.write("<html>\n")
        self.fd.write("<head>\n")
        self.fd.write("<meta charset=\"UTF-8\">\n")
        # Link style-sheet with a relative path based on where the
        # output report file will be
        self.fd.write("<link rel=\"stylesheet\" href=\"file:%s\">\n" %
                      os.path.relpath(os.path.join(sys.path[0],
                                                   "docs",
                                                   "style.css"),
                                      os.path.dirname(
                                          os.path.abspath(self.filename))).
                      replace("\\", "/"))
        self.fd.write("<title>MISS_HIT Report</title>\n")
        self.fd.write("</head>\n")
        self.fd.write("<body>\n")
        self.fd.write("<header>MISS_HIT Report</header>\n")
        self.fd.write("<main>\n")
        self.fd.write("<div></div>\n")
        self.fd.write("<h1>Issues identified</h1>\n")
        self.fd.write("<section>\n")

    def emit_message(self, message):
        self.setup_fd()

        if self.last_file != message.location.filename:
            self.last_file = message.location.filename
            self.fd.write("<h2>%s</h2>\n" % message.location.filename)

        mtext = message.message
        if message.fixed and self.autofix:
            mtext += " [fixed]"

        self.fd.write("<div class=\"message\">")
        if message.location.col_start:
            self.fd.write("<a href=\"matlab:opentoline('%s', %u, %u)\">" %
                          (message.location.filename,
                           message.location.line,
                           message.location.col_start + 1))
            self.fd.write("%s: line %u:" % (message.location.filename,
                                            message.location.line))
        elif message.location.line:
            self.fd.write("<a href=\"matlab:opentoline('%s', %u)\">" %
                          (message.location.filename,
                           message.location.line))
            self.fd.write("%s: line %u:" % (message.location.filename,
                                            message.location.line))
        else:
            self.fd.write("<a href=\"matlab:opentoline('%s')\">" %
                          message.location.filename)
            self.fd.write("%s:" % message.location.filename)
        self.fd.write("</a>")

        if message.kind == "check":
            self.fd.write(" %s (%s):" % (message.kind,
                                         message.severity))
        else:
            self.fd.write(" %s:" % message.kind)

        self.fd.write(" %s" % html.escape(message.message))

        self.fd.write("</div>\n")

    def emit_summary(self):
        self.setup_fd()
        super().emit_summary()
        if not (self.style_issues or self.warnings or self.errors):
            self.fd.write("<div>Everything is fine :)</div>")
        self.fd.write("</section>\n")
        self.fd.write("</main>\n")
        self.fd.write("</body>\n")
        self.fd.write("</html>\n")
        self.fd.close()
        self.fd = None


class JSON_Message_Handler(File_Based_Message_Handler):
    def __init__(self, tool_id, filename):
        super().__init__(tool_id, filename)
        self.blob = None

    def fork(self):
        rv = JSON_Message_Handler(self.tool_id, self.filename)
        self.fork_copy_attributes(rv)
        return rv

    def setup_fd(self):
        if self.fd is not None:
            return

        self.fd = open(self.filename, "w")
        self.blob = {}

    def emit_message(self, message):
        self.setup_fd()

        if message.location.filename not in self.blob:
            self.blob[message.location.filename] = []

        self.blob[message.location.filename].append(message.to_json())

    def emit_summary(self):
        self.setup_fd()
        super().emit_summary()
        json.dump(self.blob, self.fd, indent=2)
        self.fd.write("\n")
        self.fd.close()
