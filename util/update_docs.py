#!/usr/bin/env python3

import sys
import html
sys.path.append("..")

from miss_hit import mh_style

def offset(section):
    offsets = []
    for l in section:
        offsets.append(len(l) - len(l.lstrip()))
    return min(offsets)

def process_rule(lines, rule):
    doc = rule.__class__.__doc__.splitlines()
    short_name = doc[0].strip()
    assert doc[1].strip() == ""

    sections = [[]]
    in_code = False
    for l in doc[2:]:
        if l.strip() == "```":
            in_code = not in_code
            if in_code:
                sections.append(["```"])
            else:
                sections.append([])
        elif l.strip():
            sections[-1].append(l)
        else:
            sections.append([])
    sections = [s for s in sections if s]

    if rule.mandatory:
        lines.append("      <h4>%s</h4>" % short_name)
    else:
        lines.append("      <h4>%s (\"%s\")</h4>" % (short_name,
                                                     rule.name))

    for s in sections:
        lines.append("      <div>")
        if s[0] == "```":
            gobble = offset(s[1:])
            lines.append("<pre>")
            for l in s[1:]:
                lines.append(html.escape(l[gobble:]))
            lines.append("</pre>")
        else:
            for l in s:
                lines.append(" " * 8 + html.escape(l.strip()))
        lines.append("      </div>")
        lines.append("")

    if getattr(rule, "parameters", None):
        lines.append("      <div>")
        lines.append("        Configuration parameters:")
        lines.append("        <ul>")
        for param in rule.parameters:
            lines.append("          <li>")
            lines.append("            <b>%s</b>: %s" %
                         (param,
                          rule.parameters[param]["help"]))
            lines.append("          </li>")
        lines.append("        </ul>")
        lines.append("      </div>")
        lines.append("")

def process(lines, rules):
    sorted_rules = [r
                    for _, r in sorted((rule.__class__.__name__, rule)
                                       for rule in rules)]
    for rule in sorted_rules:
        process_rule(lines, rule)

def main():
    rule_set = mh_style.get_rules()
    rules = [rule()
             for rules in rule_set.values()
             for rule in rules]

    mandatory_rules = [rule
                       for rule in rules
                       if rule.mandatory]
    autofix_rules = [rule
                     for rule in rules
                     if not rule.mandatory and rule.autofix]
    other_rules = [rule
                   for rule in rules
                   if not rule.mandatory and not rule.autofix]

    lines = []
    in_section = False
    with open("../docs/style_checker.html", "r") as fd:
        for raw_line in fd:
            if "END HOOK: " in raw_line:
                assert in_section
                in_section = False
                if "MANDATORY RULES" in raw_line:
                    process(lines, mandatory_rules)
                elif "AUTOFIX RULES" in raw_line:
                    process(lines, autofix_rules)
                else:
                    process(lines, other_rules)
            elif "HOOK: " in raw_line:
                assert not in_section
                in_section = True
                lines.append(raw_line.rstrip())

            if not in_section:
                lines.append(raw_line.rstrip())

    with open("../docs/style_checker.html", "w") as fd:
        fd.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
