[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3967056.svg)](https://doi.org/10.5281/zenodo.3967056)

# MATLAB Independent, Small & Safe, High Integrity Tools

http://misshit.org

MATLAB is a popular programming language in many engineering
disciplines, intended for the fast development of prototypes. But as
we all know, prototypes make it into production all the time, so now
you're stuck. Unfortunately, there are no style checkers or "good"
static analysis tools for MATLAB. This project attempts to fill this
gap.

If you have MATLAB (or MATLAB embedded in Simulink models) in your
production code and want to improve code quality then this tool-suite
is for you.

## Tools & Documentation

MISS_HIT comes with the following tools, all of which come with user
manuals and setup instructions:
https://florianschanda.github.io/miss_hit/

* Style Checker `mh_style`

  A simple coding style checker and code formatter for MATLAB or
  Octave code, including MATLAB embedded inside Simulink models.

* Code Metrics `mh_metric`

  A simple code metric tool for MATLAB or Octave code, including
  MATLAB embedded inside Simulink models.

* Bug finding `mh_lint`

  A simple linter for MATLAB or Octave code, including
  MATLAB embedded inside Simulink models.

* Code/Test traceability `mh_trace`

  A simple tool to extrace tags from test and code to demonstrate
  requirements traceability.

* Diff helper `mh_diff`

  A tool for diffing MATLAB code inside Simulink models. Note that
  other changes (e.g. different connections) are not detected; this is
  only working for embedded MATLAB.

* Copyright notice helper `mh_copyright`

  A tool that can update or adjust copyright notices in bulk. Helpful
  if your company changes name, or you have year ranges that need
  updating.

Please refer to the [release notes](https://github.com/florianschanda/miss_hit/blob/master/CHANGELOG.md)
for a summary of recent changes and known issues.

We intend to provide more tools later, please refer to the
[roadmap](https://github.com/florianschanda/miss_hit/blob/master/ROADMAP.md)
for more information.

## Installing and using MISS_HIT

### Installation via pip

```
$ pip3 install --user miss_hit
```

This installation also adds five executable scripts `mh_style`,
`mh_metric`, `mh_lint`, `mh_copyright`, and `mh_diff` into
`.local/bin`, so please make sure that this is on your `PATH`.

You can also use the `python -m` syntax to directly invoke the
program. This might be useful if you're on a heavily locked-down
corporate Windows environment:
```
$ python3 -m miss_hit.mh_style
```

To use MISS_HIT you just give it a set of files or directories to
process, for example:
```
$ mh_style my_file.m
$ mh_style --process-slx my_model.slx
$ mh_style src/
```

Configuration and setup is described in the
[user manuals](https://florianschanda.github.io/miss_hit)

### Installation by checkout

It is recommended to use pip, as that gets you the latest stable
release. However, it is possible to directly use MISS_HIT from a
checkout.  MISS_HIT does not require *any* python packages or
libraries. Just check out the repository and put it on your
path. That's it.

The version of Python I am using is `3.6` but any later version should
also work. I am not using any overly fancy language features.

### Additional requirements for developing MISS_HIT

If you want to help develop you will need Linux as the test-suite
doesn't really work on Windows. You will also need Pylint,
PyCodeStyle, Coverage, and Graphviz. Install as follows:

```
$ apt-get install graphviz
$ pip3 install --user --upgrade pylint pycodestyle coverage
```

For publishing releases (to GitHub and PyPI) you will also need:
```
$ pip3 install --user --upgrade setuptools wheel requests
```

## Challenges

There are serious issues present in the MATLAB and Octave languages on
all levels (lexical structure, parsing, and semantics) that make it
very difficult to create any tool processing them. In fact, GitHub is
littered with incomplete attempts and buggy parsers. The usual
question is "but what about Octave?"; it is a similar language, but it
is not compatible with MATLAB. If your problem is parsing MATLAB then
the Octave parser will not help you. Even very simple statements such
as `x = [1++2]` mean different things (`3` in MATLAB, syntax error in
Octave).

I have [documented the key
issues](https://github.com/florianschanda/miss_hit/blob/master/CHALLENGES.md)
we've faced and how we've resolved them.

## Copyright & License

The basic framework, style checker and code metrics tool of MISS_HIT
(everything under `miss_hit_core`) are licensed under the GNU GPL
version 3 (or later) as described in
[LICENSE](https://github.com/florianschanda/miss_hit/blob/master/LICENSE).

The advanced analysis tools of MISS_HIT (everything under `miss_hit`)
are licensed under the GNU Affero GPL version 3 (or later) as
described in
[LICENSE.AGPL](https://github.com/florianschanda/miss_hit/blob/master/LICENSE.AGPL).

The vast majority of this work is (C) Florian Schanda. Contributions
from the following people and entities are under their copyright, with
the same license:

* Alina Boboc (Documentation style)
* Benedikt Schmid (MATLAB integration)
* Remi Gau (CI/CD templates)
* Veoneer System Software GmbH (JSON Metrics)
* Zenuity AB (Key parts of the lexer)

### Copyright of octave tests

This project includes modified/adapted parts of the GNU Octave
testsuite under `tests/parser/octave_*`. These are (c) their original
authors. Each file there describes from which file they derive.

### Note on parser tests

Some of the parser tests include code samples and documentation
snippets from the publicly available MathWorks website. An
attribution (in comment form) is always included in these cases.

### Note on the documentation assets

The documentation uses
[feather icons](https://github.com/feathericons/feather/blob/master/LICENSE)
which are licensed under the MIT License.
