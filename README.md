# MATLAB Independent, Small & Safe, High Integrity Tools

Let's face it: MATLAB (R) and Octave are probably the worst
programming language ever invented that aren't weird on purpose
(e.g. Malbolge). They are the only languages I know of where the
lexing is context sensitive and pretty much every single feature is
conceived to make the task of writing MATLAB (R) / Octave programs, or
analysis tools as difficult and error-prone as possible. In my opinion
JavaScript compares favourably, since that has at least published
language grammar and semantics; a task which The MathWorks has refused
to undertake for at least 20 years.

MATLAB (R) for all its faults it is however a pretty good prototyping
tool, and is pervasive in engineering disciplines. However it should
never be used for anything real, ever. But as we all know, prototypes
make it into production all the time, so now you're now stuck in a
living hell of legacy code.

If this is you, then this tool suite is for you.

## Tools

### Style Checker

A simple style checker exists (mh_style.py). It can detect and correct
(when the `--fix` options given) a number of coding style issues.

* Max lines in file (configurable with `--file-length`, default is
  1000)

* Max character per line (configurable with `--line-length`, default
  is 80)

* Copyright notice in the form of `(C) Copyright YEAR-YEAR ENTITY` or
  `(C) Copyright YEAR ENTITY`. The list of acceptable entities can be
  configured with `--copyright-entity`.

* (autofix) More than one consecutive blank line

* (autofix) Trailing whitespace

* (autofix) Whitespace around the assignment operation (=)

* (autofix) No whitespace after opening brackets '(', and no
  whitespace before closing brackets ')'

* (autofix) Whitespace after certain words such as 'if' or 'properties'.

* (autofix) Use of tab anywhere (adjust with `--tab-width`)

* Ending a line with a comma

The style checker attempts to read a configuration file `miss_hit.cfg`
in the current directory. If one cannot be found we traverse the tree
up intil we find one or hit the filesystem root. The syntax is
simple. For example:

```
# Like the commandline, but with _ instead of _
line_length: 100
copyright_entity: "Lord Buckethead"
```

## Infrastructure

### Lexer

The lexer is mostly working, but it does not yet deal with matrices or
cells correctly. Specifically things it is currently impossible to
distinguish between [1+ 1] and [1 +1]. I plan to fix this eventually
by adding anonymous commas in the lexer.

### Parser

The parser is extremely incomplete and is work in progress. It is not
yet useful, but trivial example programs are parsed correctly. There
are many known bugs.

## Road map

This project is a labour of love (or hate, the two have been remarked
on being sufficiently similar by many philosophers). Progress will not
be amazingly fast. Things I intend to publish, not necessarily in this
order:

* A grammar for a subset of the language accepted by MATLAB (R) or GNU
  Octave. The MATLAB (R) code generator requires a subset anyway, so
  most people are used to the idea of subsets already.

* A lexer and parser for this subset, written in Python.

* Safe semi-formal semantics, which may not be the officially correct
  ones, but which should over-approximate the real ones. This means
  that they may be much stricter than what you might be able to do,
  but if the tool indicates it's safe here then it's safe for real
  too.

* A style checker in the tradition of simple lint tools (checks
  indentation, naming schemes, white space). This tool would also
  enforce the "safe" subset by virtue of refusing to parse offensive
  constructs such as [1+ + +1]

* A data-flow analysis tool to detect e.g. unused or uninitalised
  variables.

* A code generator (intended targets C and SPARK) which doesn't
  suck. If you want an example of what sucks, just look at what MATLAB
  (R) does with mod(a, b), and then you know why this is needed.

* A VC generation tool (either under-approximate BMC or deductive).

* A qualification pack.

## Correctness

How do I know that the intended semantics are correct, since The
MathWorks have refused to publish or document the intended semantics
of MATLAB (R)?

Short answer: I don't.

Long answer: We can get it mostly right by carefully sub-setting the
language to rule out weird cases and creating set of test programs
which can be run in MATLAB (R) or GNU Octave to make sure all
assumptions for this subset are correct for that specific version of
MATLAB (R) or GNU Octave.

This approach is more or less what you do when you qualify a tool or
compiler for use in your safety critical project.

## Copyright

Most of this work is (C) Florian Schanda and is licensed under the GNU
GPL version 3 as described in LICENSE.

Contributions from the following people and entities are under their
copyright, with the same license:

* Zenuity AB
