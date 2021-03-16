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
##  free software: you can redistribute it and/or modify                    ##
##  it under the terms of the GNU Affero General Public License as          ##
##  published by the Free Software Foundation, either version 3 of the      ##
##  License, or (at your option) any later version.                         ##
##                                                                          ##
##  MISS_HIT is distributed in the hope that it will be useful,             ##
##  but WITHOUT ANY WARRANTY; without even the implied warranty of          ##
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           ##
##  GNU Afferto General Public License for more details.                    ##
##                                                                          ##
##  You should have received a copy of the GNU Affero General Public        ##
##  License along with MISS_HIT. If not, see                                ##
##  <http://www.gnu.org/licenses/>.                                         ##
##                                                                          ##
##############################################################################

import datetime

from miss_hit_core import command_line
from miss_hit_core import work_package
from miss_hit_core.m_ast import *
from miss_hit_core.errors import Error, Message_Handler, ICE
from miss_hit_core.m_lexer import MATLAB_Lexer


def year_span_key(blob):
    a_start, a_end, a_org = blob

    if a_start is None:
        a_start = a_end

    return (a_start, a_end, a_org)


class MH_Copyright_Result(work_package.Result):
    def __init__(self, wp, processed=False):
        super().__init__(wp, processed)


class MH_Copyright(command_line.MISS_HIT_Back_End):
    def __init__(self):
        super().__init__("MH Copyright")

    @classmethod
    def process_wp(cls, wp):
        # Load file content
        content = wp.get_content()
        is_embedded = isinstance(wp, work_package.Embedded_MATLAB_WP)

        # Deal with command-line options
        primary_entity = wp.cfg.style_config["copyright_primary_entity"]
        if wp.options.primary_entity:
            primary_entity = wp.options.primary_entity
        old_entity = None
        if wp.options.update_year:
            action = "update_year"
        elif wp.options.merge:
            action = "merge"
        elif wp.options.change_entity is not None:
            action = "change_entity"
            old_entity = wp.options.change_entity
        elif wp.options.add_notice:
            action = "add_notice"
        else:
            raise ICE("none of the action are set")

        # Create lexer
        lexer = MATLAB_Lexer(wp.mh, content, wp.filename, wp.blockname)
        if wp.cfg.octave:
            lexer.set_octave_mode()
        if not wp.cfg.pragmas:  # pragma: no cover
            lexer.process_pragmas = False

        # We're dealing with an empty file here. Lets just not do anything
        if len(lexer.text.strip()) == 0:
            return MH_Copyright_Result(wp, False)

        # Determine primary copyright holder. We use the command-line,
        # or try and deduce from the config files.
        if not primary_entity:
            if len(wp.cfg.style_config["copyright_entity"]) == 1:
                primary_entity = \
                    list(wp.cfg.style_config["copyright_entity"])[0]
            else:
                wp.mh.warning(lexer.get_file_loc(),
                              "unable to determine primary copyright entity,"
                              " skipping this file")
                return MH_Copyright_Result(wp, False)

        # Compile magic regex
        cr_regex = re.compile(wp.cfg.style_config["copyright_regex"])

        # Process tokens and take actions
        try:
            # Determine where the actual file content starts, and a
            # list of all copyright info.
            in_copyright_notice = (
                wp.cfg.active("copyright_notice") and
                (not is_embedded or
                 wp.cfg.style_config["copyright_in_embedded_code"]))
            old_copyright_info = []
            file_start = 1
            newlines = 1
            comment_char = "%"
            while in_copyright_notice:
                token = lexer.token()
                if token is None:
                    in_copyright_notice = False
                elif token.kind == "COMMENT":
                    match = cr_regex.search(token.value)
                    if match:
                        if not token.raw_text.startswith("%"):
                            comment_char = token.raw_text[0]
                        old_copyright_info.append(
                            (int(match.group("ystart"))
                             if match.group("ystart")
                             else None,
                             int(match.group("yend")),
                             match.group("org"),
                             token))
                        file_start = token.location.line + 1
                    else:
                        file_start = token.location.line
                        in_copyright_notice = False
                elif token.kind == "NEWLINE":
                    newlines = len(token.value)
                else:
                    # Once we get a non-comment/non-copyright token,
                    # the header has ended. We then emit messages if
                    # we could not find anything.
                    in_copyright_notice = False
                    file_start = token.location.line

            # Update notices as instructed
            copyright_info = []
            action_taken = False
            merged_copyright = [None, None, primary_entity]
            original_primary = None
            for ystart, yend, org, token in old_copyright_info:
                if ystart is not None and ystart > yend:
                    wp.mh.error(token.location,
                                "initial year is later than end year")

                if action == "update_year":
                    if org == primary_entity:
                        if yend < wp.options.year:
                            if ystart is None:
                                ystart = yend
                            yend = wp.options.year
                            action_taken = True
                        elif yend > wp.options.year:
                            wp.mh.error(token.location,
                                        "end year is later than %u" %
                                        wp.options.year)

                        if ystart is not None:
                            if ystart == yend:
                                ystart = None
                                action_taken = True
                    copyright_info.append((ystart, yend, org))

                elif action == "change_entity":
                    if org == old_entity:
                        org = primary_entity
                        action_taken = True
                    copyright_info.append((ystart, yend, org))

                elif action == "merge":
                    if org in wp.cfg.style_config["copyright_entity"] or \
                       org == primary_entity:
                        # Actions are definitely taken if we have multiple
                        # primaries, or we have a non-primary entity
                        if org == primary_entity:
                            if original_primary is None:
                                original_primary = (ystart, yend, org)
                            else:
                                action_taken = True
                        else:
                            action_taken = True

                        # Update the merged entity
                        if merged_copyright[0] is None:
                            merged_copyright[0] = ystart
                        elif ystart is not None:
                            merged_copyright[0] = min(merged_copyright[0],
                                                      ystart)

                        if merged_copyright[0] is None:
                            merged_copyright[0] = yend
                        else:
                            merged_copyright[0] = min(merged_copyright[0],
                                                      yend)

                        if merged_copyright[1] is None:
                            merged_copyright[1] = yend
                        else:
                            # yend is always not None
                            merged_copyright[1] = max(merged_copyright[1],
                                                      yend)
                    else:
                        copyright_info.append((ystart, yend, org))

                elif action == "add_notice":
                    copyright_info.append((ystart, yend, org))

                else:
                    raise ICE("unexpected action %s" % action)

            # Final updates for the merge and add action
            if action == "merge" and merged_copyright[1] is not None:
                # Clean merged copyright
                if merged_copyright[0] == merged_copyright[1]:
                    merged_copyright[0] = None

                # Add new entry and sort list chronologically
                copyright_info.append(tuple(merged_copyright))
                copyright_info.sort(key=year_span_key)

                # Check if we'd actually change anything
                if not action_taken and \
                   tuple(merged_copyright) != original_primary:
                    action_taken = True

            elif action == "add_notice":
                if len(copyright_info) == 0:
                    copyright_info.append((None,
                                           wp.options.year,
                                           primary_entity))
                    action_taken = True

            # Re-build file header
            if action_taken:
                new_content = []
                for ystart, yend, org in copyright_info:
                    sub = {"ystart" : ystart,
                           "yend" : yend,
                           "org"  : org}
                    if ystart is None:
                        new_content.append("%s %s" %
                                           (comment_char,
                                            wp.options.template % sub))
                    else:
                        new_content.append("%s %s" %
                                           (comment_char,
                                            wp.options.template_range % sub))
                if newlines >= 2 or action == "add_notice":
                    new_content.append("")
                new_content += lexer.context_line[file_start - 1:]

                wp.write_modified("\n".join(new_content) + "\n")
                return MH_Copyright_Result(wp, True)

            else:
                wp.mh.info(lexer.get_file_loc(), "no action taken")
                return MH_Copyright_Result(wp, False)

        except Error:
            # If there are any errors, we can stop here
            return MH_Copyright_Result(wp, False)


def main_handler():
    clp = command_line.create_basic_clp(
        epilog=("Remember to carefully review any code changes this tool"
                " makes, as copyright notices are generally considered to"
                " be quite important."))

    clp["ap"].add_argument("--process-slx",
                           action="store_true",
                           default=False,
                           help=("Update copyright notices inside Simulink"
                                 " models. This option is temporary, and"
                                 " will be removed in future once the"
                                 " feature is good enough to be enabled"
                                 " by default."))

    c_actions = clp["ap"].add_argument_group("copyright action")
    c_actions = c_actions.add_mutually_exclusive_group(required=True)
    c_actions.add_argument("--update-year",
                           action="store_true",
                           default=False,
                           help=("Update the end year in copyright notices for"
                                 " the primary copyright holder to the current"
                                 " year."))
    c_actions.add_argument("--merge",
                           action="store_true",
                           default=False,
                           help=("Merge all non-3rd party copyright notices"
                                 " into one for the primary copyright holder"))
    c_actions.add_argument("--change-entity",
                           default=None,
                           metavar="OLD_COPYRIGHT_HOLDER",
                           help=("Change notices from the specified copyright"
                                 " holder into the primary copyright holder."))
    c_actions.add_argument("--add-notice",
                           action="store_true",
                           default=False,
                           help=("Add a copyright notice to files that do not"
                                 " have one yet."))

    c_data = clp["ap"].add_argument_group("copyright data")
    c_data.add_argument("--year",
                        default=datetime.datetime.now().year,
                        type=int,
                        help=("The current year (by default this is"
                              " %(default)s)"))
    c_data.add_argument("--primary-entity",
                        default=None,
                        metavar="COPYRIGHT_HOLDER",
                        help=("The primary copyright entity."))
    c_data.add_argument("--template-range",
                        default="(c) Copyright %(ystart)u-%(yend)u %(org)s",
                        metavar="TEMPLATE_TEXT",
                        help=("Text template to use for a copyright notice"
                              " with a year range. default: '%(default)s'"))
    c_data.add_argument("--template",
                        default="(c) Copyright %(yend)u %(org)s",
                        metavar="TEMPLATE_TEXT",
                        help=("Text template to use for a copyright notice"
                              " with a single year. default: '%(default)s'"))

    options = command_line.parse_args(clp)

    # Sanity check year
    if options.year < 1900:  # pragma: no cover
        clp["ap"].error("year must be at lest 1900")
    elif options.year >= 10000:  # pragma: no cover
        clp["ap"].error("I am extremely concerned that this tool is still"
                        " useful after 8000 years, stop what you're doing"
                        " and change programming language NOW.")

    mh = Message_Handler("copyright")

    mh.show_context = not options.brief
    mh.show_style   = False
    mh.show_checks  = False
    mh.autofix      = True

    copyright_backend = MH_Copyright()
    command_line.execute(mh, options, {},
                         copyright_backend,
                         options.process_slx)


def main():
    command_line.ice_handler(main_handler)


if __name__ == "__main__":  # pragma: no cover
    main()
