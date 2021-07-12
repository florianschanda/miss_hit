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
from miss_hit_core.m_lexer import MATLAB_Lexer, Token_Buffer
from miss_hit_core.m_parser import MATLAB_Parser
from miss_hit_core.m_parse_utils import parse_docstrings


def get_primary_entity(options, cfg):
    if options.primary_entity:
        primary_entity = options.primary_entity
    else:
        primary_entity = cfg.style_config["copyright_primary_entity"]

    if not primary_entity and len(cfg.style_config["copyright_entity"]) == 1:
        primary_entity = list(cfg.style_config["copyright_entity"])[0]

    return primary_entity


def replace_line(lines, line_no, block_comment,
                 templates, copy_note, org, year_range,
                 offset=None):
    assert isinstance(lines, list)
    assert isinstance(line_no, int) and 1 <= line_no <= len(lines)
    assert isinstance(block_comment, bool)
    assert isinstance(templates, dict)
    assert isinstance(copy_note, str)
    assert isinstance(org, str)
    assert isinstance(year_range, tuple) and len(year_range) == 2
    assert isinstance(year_range[0], int)
    assert isinstance(year_range[1], int)
    assert offset is None or (isinstance(offset, int) and offset >= 0)

    # Replacing lines needs to do two things in order not to mess up
    # any existing formatting.
    #   1. Match the previous indentation
    #   2. Match the previous offset after the comment character

    old_line = lines[line_no - 1]
    if block_comment:
        old_indent = ""
        old_offset = re.match("^[ \t]*", old_line).group(0)
        comment_char = ""
    else:
        old_indent = re.match("^[ \t]*", old_line).group(0)
        old_offset = re.match("^[ \t]*",
                              old_line[len(old_indent) + 1:]).group(0)
        comment_char = old_line[len(old_indent)]

    if offset is not None:
        old_offset = " " * offset

    data = {"copy"   : copy_note,
            "org"    : org,
            "ystart" : year_range[0],
            "yend"   : year_range[1]}

    new_line = old_indent + comment_char + old_offset
    if year_range[0] == year_range[1]:
        new_line += templates["single"] % data
    else:
        new_line += templates["range"] % data

    lines[line_no - 1] = new_line


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

        # Create lexer
        lexer = MATLAB_Lexer(wp.mh, content, wp.filename, wp.blockname)
        if wp.cfg.octave:
            lexer.set_octave_mode()
        if not wp.cfg.pragmas:  # pragma: no cover
            lexer.process_pragmas = False

        # Deal with command-line options, setting up three variables:
        # * action - what to do
        # * primary_entity - main entity
        # * templates - how to write copyright notices
        templates = {"single" : wp.options.template,
                     "range"  : wp.options.template_range}
        primary_entity = get_primary_entity(wp.options, wp.cfg)
        if not primary_entity:
            wp.mh.warning(lexer.get_file_loc(),
                          "unable to determine primary copyright entity,"
                          " skipping this file")
            return MH_Copyright_Result(wp, False)
        if wp.options.update_year:
            action = "update_year"
        elif wp.options.merge:
            action = "merge"
        elif wp.options.change_entity is not None:
            action = "change_entity"
        elif wp.options.add_notice:
            action = "add_notice"
        else:
            raise ICE("none of the action are set")

        allowed_entities = (wp.cfg.style_config["copyright_entity"] |
                            set([primary_entity]))

        # We're dealing with an empty file here. Lets just not do anything
        if len(lexer.text.strip()) == 0:
            return MH_Copyright_Result(wp, False)

        # Parse
        try:
            tbuf = Token_Buffer(lexer, wp.cfg)
            parser = MATLAB_Parser(wp.mh, tbuf, wp.cfg)
            parse_tree = parser.parse_file()
            parse_docstrings(wp.mh, wp.cfg, parse_tree, tbuf)
        except Error:  # pragma: no cover
            return MH_Copyright_Result(wp, False)

        # Determine the docstring of the primary entity. We use the
        # script/class docstring, if it exists and contains copyright
        # info. Otherwise we use the compilation unit's docstring
        # (i.e. file header). The style checker worries about the case
        # where we have copyright in more than one location.
        n_docstring = None
        if isinstance(parse_tree, Class_File):
            n_docstring = parse_tree.n_classdef.n_docstring
        elif isinstance(parse_tree, Function_File):
            n_docstring = parse_tree.l_functions[0].n_docstring
        if n_docstring is None or not n_docstring.copyright_info:
            n_docstring = parse_tree.n_docstring
        # Note that n_docstring could be None at this point, so we do
        # need to deal with that correctly.

        # Set up line -> Copyright_Info map
        cinfos = {}
        if n_docstring:
            for cinfo in n_docstring.copyright_info:
                if cinfo.t_comment.location.line in cinfos:
                    raise ICE("docstring with duplicate line (%u)" %
                              cinfo.t_comment.location.line)
                else:
                    cinfos[cinfo.t_comment.location.line] = cinfo

            # The merge action requires the copyright notice to be
            # grouped. Enforce this now.
            if action == "merge" and \
               not (n_docstring.all_copyright_in_one_block(allowed_entities) or
                    n_docstring.all_copyright_in_one_block()):
                wp.mh.error(n_docstring.loc(),
                            "cannot merge entries in this docstring as they"
                            " are not all next to each other",
                            fatal=False)
                return MH_Copyright_Result(wp, False)

        # Perform actions
        action_taken = False
        lines = copy(lexer.context_line)
        try:
            if action == "update_year":
                new_year = wp.options.year
                for line_no, cinfo in cinfos.items():
                    ystart, yend = cinfo.get_range()
                    if cinfo.get_org() != primary_entity:
                        continue

                    if yend <= new_year:
                        new_range = (ystart, new_year)
                        replace_line(lines, line_no, cinfo.is_block_comment(),
                                     templates, cinfo.get_copy_notice(),
                                     primary_entity, new_range)

                        action_taken = True
                    else:
                        wp.mh.error(cinfo.loc_yend(),
                                    "end year is later than %s" % new_year)

            elif action == "merge":
                merged_line = None
                merged_line_is_block = None
                killed_lines = []
                new_range = None
                for line_no in sorted(cinfos):
                    cinfo = cinfos[line_no]
                    ystart, yend = cinfo.get_range()

                    if cinfo.get_org() not in allowed_entities:
                        continue
                    if cinfo.get_org() != primary_entity or ystart == yend:
                        action_taken = True

                    if ystart > yend:
                        wp.mh.error(cinfo.loc_ystart(),
                                    "initial year is later than end year")

                    if new_range is None:
                        merged_line = line_no
                        merged_line_is_block = cinfo.is_block_comment()
                        merged_line_copy_notice = cinfo.get_copy_notice()
                        new_range = cinfo.get_range()
                    else:
                        new_range = (min(ystart, new_range[0]),
                                     max(yend, new_range[1]))
                        killed_lines.append(line_no)
                        action_taken = True

                if action_taken:
                    replace_line(lines, merged_line, merged_line_is_block,
                                 templates, merged_line_copy_notice,
                                 primary_entity, new_range)
                    for line_no in reversed(killed_lines):
                        del lines[line_no - 1]

            elif action == "change_entity":
                for line_no, cinfo in cinfos.items():
                    if cinfo.get_org() == wp.options.change_entity:
                        replace_line(lines, line_no, cinfo.is_block_comment(),
                                     templates, cinfo.get_copy_notice(),
                                     primary_entity,
                                     cinfo.get_range())
                        action_taken = True

            elif action == "add_notice":
                # Only add copyright notices to files without any
                # notice.
                if len(cinfos) == 0:
                    # Find the right place to add the notice. Right
                    # now we only do this for the file header; so we
                    # need to find it and append at the end; or create
                    # a new one.
                    action_taken = True

                    if parse_tree.n_docstring:
                        is_block, line_no = parse_tree.n_docstring.final_line()
                        off = parse_tree.n_docstring.guess_docstring_offset()

                        # Duplicate the last line
                        lines = \
                            lines[:line_no] + \
                            [lines[line_no - 1]] + \
                            lines[line_no:]
                    else:
                        is_block = False
                        line_no = 0
                        off = 1
                        lines = ["% POTATO", ""] + lines

                    if wp.options.style == "c_first" or \
                       (wp.options.style == "dynamic" and
                        not wp.cfg.octave):
                        copy_notice = "(c) Copyright"
                    else:
                        copy_notice = "Copyright (c)"

                    # Then overwrite it
                    replace_line(lines, line_no + 1, is_block,
                                 templates, copy_notice, primary_entity,
                                 (wp.options.year, wp.options.year),
                                 offset = off)

            else:
                raise ICE("Unexpected action '%s'" % action)
        except Error:
            return MH_Copyright_Result(wp, False)

        if action_taken:
            wp.write_modified("\n".join(lines) + "\n")

        return MH_Copyright_Result(wp, True)


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
    c_actions.add_argument("--style",
                           choices=("dynamic", "c_first", "c_last"),
                           default="dynamic",
                           help=("'(c) Copyright' or 'Copyright (c)'. Dynamic"
                                 " picks the existing style, and if there is"
                                 " nothing, picks c_first for MATLAB code and"
                                 " c_last for Octave code."
                                 " Default is %(default)s."))

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
                        default="%(copy)s %(ystart)u-%(yend)u %(org)s",
                        metavar="TEMPLATE_TEXT",
                        help=("Text template to use for a copyright notice"
                              " with a year range. default: '%(default)s'"))
    c_data.add_argument("--template",
                        default="%(copy)s %(yend)u %(org)s",
                        metavar="TEMPLATE_TEXT",
                        help=("Text template to use for a copyright notice"
                              " with a single year. default: '%(default)s'"))

    options = command_line.parse_args(clp)

    # Sanity check year
    if options.year < 1000:  # pragma: no cover
        clp["ap"].error("year must be at lest 1000")
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
