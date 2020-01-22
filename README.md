# MATLAB Independent, Small & Safe, High Integrity Tools

Let's face it: MATLAB (R) and Octave are probably the worst
programming language ever invented that aren't weird on purpose
(e.g. Malbolge). They are the only languages I know of where the
lexing is context sensitive with potentially unlimited lookahead and
pretty much every single feature appears to be conceived to make the
task of writing analysis tools for MATLAB (R) / Octave programs as
difficult and error-prone as possible. In my opinion JavaScript and
PHP compare favourably from an analysis point of view, since that has
at least published language grammar and semantics; a task which The
MathWorks has not undertaken so far.

MATLAB (R) for all its faults it is however a pretty good prototyping
tool, and is pervasive in many engineering disciplines. However it
should never be used for anything approaching production, ever. But as
we all know, prototypes make it into production all the time, so now
you're now stuck.

If this is you, then this tool suite is for you.

## Tools

All tools are documented here:
https://florianschanda.github.io/miss_hit/

### Style Checker

A simple coding style checker for MATLAB. See
https://florianschanda.github.io/miss_hit/style_checker.html for more
information and a user manual.

## Infrastructure

### Lexer

The Lexer is more or less complete and works correctly. The following
difficult features/bugs of the MATLAB (R) are fully supported:

* Adding anonymous commas in matrices, so that the parser will always
  see a comma-separated row and does not have to care about
  whitespace. So `[1 1]` will be lexed to `[1, 1]`.

* Distinguishing ' (transpose) from ' (single-quoted character array)

* Support for lambda functions inside matrix/cells (think about the
  extra special treatment of whitespace in `{@(x) 1}`)

* Support for weird matrices (e.g. `[1 +1]` and `[1 ++1]` are lexed
  correctly)

* Distinguishing between matrices and assignment lists

* Command form transformation (e.g. `foo bar (baz)` is lexed as
  identifier `foo`, char array `bar`, and char array
  `(baz)`. Including the bugs/weirdness like `f) o[[ b` lexing as a
  single string. Including the really bizarre stuff like `f''] %`
  lexing as `f] ` (with a trailing space).

* Classdef blocks (e.g. `foo uint8` is not lexed as command form, but
  correctly as two identifiers).

* Block comments (with all the unspecified weirdness of nesting them
  or including text on the same line).

The notable missing features can be found in our [lexer issues](https://github.com/florianschanda/miss_hit/issues?q=is%3Aopen+is%3Aissue+label%3A%22component%3A+lexer%22).

### Parser

The parser is mostly complete, but it only parses (no semantic
analysis). Three of the most starred projects on github using MATLAB
(R) or Octave are processed without parse errors (matconvnet,
matlab2tikz, MatlabFunc).

I am working on ironing out some of the more obscure bugs before
moving on to basic semantic analysis (starting with name resolution
and basic type analysis).

## Road map

This project is a labour of love (or hate, the two have been remarked
on being sufficiently similar by many philosophers). Progress will not
be amazingly fast. Things I intend to publish, not necessarily in this
order:

* A grammar for a subset of the language accepted by MATLAB (R) or
  Octave. The MATLAB (R) code generator requires a subset anyway, so
  most people are used to the idea of subsets already.

* A lexer and parser for this subset, written in Python.

* Safe semi-formal semantics, which may not be the officially correct
  ones, but which should over-approximate the real ones. This means
  that they may be much stricter than what you might be able to do,
  but if the tool indicates it's safe here then it's safe for real
  too.

* A style checker in the tradition of simple lint tools (checks
  indentation, naming schemes, white space).

* A data-flow analysis tool to detect e.g. unused or uninitalised
  variables.

* A code generator (intended targets C and SPARK) that precisely
  follows the documented semi-formal semantics.

* A VC generation tool (either under-approximate BMC or deductive).

* A qualification pack that maps the semi-formal semantics we decided
  to any specific MATLAB (R) version, demonstrating that the semantics
  are precisely correct or a safe over-approximation.

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

The vast majority of this work is (C) Florian Schanda and is licensed
under the GNU GPL version 3 as described in LICENSE.

Contributions from the following people and entities are under their
copyright, with the same license:

* Zenuity AB
* Alina Boboc

### Copyright of octave tests

This project includes modified/adapted parts of the GNU Octave
testsuite under `tests/parser/octave_*`. These are (c) their original
authors. Each file there describes from which file they derive.

### Note on parser tests

Some of the parser tests include code samples and documentation
snippets from the publically available MathWorks website. An
attribution (in comment form) is always included in these cases.

### Note on the documentation assets

The documentation uses
[feather icons](https://github.com/feathericons/feather/blob/master/LICENSE)
which are licensed under the MIT License.
