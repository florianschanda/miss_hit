# MATLAB Independent, Small & Safe, High Integrity Tools

MATLAB is a popular programming language in many engineering
disciplines, intended for the fast development of prototypes. But as
we all know, prototypes make it into production all the time, so now
you're stuck. Unfortunately, there are no style checkers or "good"
static analysis tools for MATLAB. This project attempts to fill this
gap.

If you have MATLAB or MATLAB embedded in Simulink models in your
production code and want to improve code quality then this tool-suite
is for you.

## Tools & Documentation

All tools and language features are documented here:
https://florianschanda.github.io/miss_hit/

We intend to provide more tools later, please refer to the
[roadmap](https://github.com/florianschanda/miss_hit/blob/master/ROADMAP.md)
for more information.

Please refer to the [release notes](https://github.com/florianschanda/miss_hit/blob/master/CHANGELOG.md)
for a summary of recent changes and known issues.

* Style Checker `mh_style`

  A simple coding style checker and code formatter for MATLAB or
  Octave code, including MATLAB embedded inside Simulink models. See
  https://florianschanda.github.io/miss_hit/style_checker.html for
  more information and a user manual.

* Code Metrics `mh_metric`

  A simple code metric tool for MATLAB or Octave code, including
  MATLAB embedded inside Simulink models. See
  https://florianschanda.github.io/miss_hit/metrics.html for more
  information and a user manual.

* Pragmas understood by MISS_HIT tools

  The tools can be controlled with some special pragmas. See
  https://florianschanda.github.io/miss_hit/pragmas.html for more
  information.

## Installing and using MISS_HIT

Just check out the repository and put it on your path. That's
it. MISS_HIT does not require *any* python packages or libraries.

To use MISS_HIT you just give it a set of files to process, for example:
```
$ mh_style my_file.m
$ mh_style --process-slx my_model.slx
```
Configuration is described in the user manual(s).

The version of Python I am using is `3.6.9` but any earlier or later
version should also work. I am not using any overly fancy language
features.

### Installation via pip

```
$ pip3 install --user miss_hit
```

This installation also adds two executable scripts `mh_style` and
`mh_metric` into `.local/bin`, so please make sure that this is on
your `PATH`.

You can also use the `python -m` syntax to directly invoke the
program. This might be useful if you're on a heavily locked-down
corporate Windows environment:
```
$ python3 -m miss_hit.mh_style
```

### Additional requirements for developing MISS_HIT

If you want to help develop, you will also need Pylint, PyCodeStyle
and Graphviz. Install as follows:
```
$ apt-get install graphviz
$ pip3 install --user pylint pycodestyle
```

## Challenges

There are serious issues present in the MATLAB and Octave languages on
all levels (lexical structure, parsing, and semantics) that make it
very difficult to create any tool processing them. In fact github is
littered with incomplete attempts and buggy parsers. The usual
question is "but what about Octave?"; it is a similar language, but it
is not compatible with MATLAB. If your problem is parsing MATLAB then
the Octave parser will not help you. Even very simple statements such
as `x = [1++2]` mean different things (`3` in MATLAB, syntax error in
Octave).

We've [documented the key
issues](https://github.com/florianschanda/miss_hit/blob/master/CHALLENGES.md)
we've faced and how we've resolved them.

## Copyright

MISS_HIT is licensed under the GNU GPL version 3 as described in
LICENSE.

The vast majority of this work is (C) Florian Schanda. Contributions
from the following people and entities are under their copyright, with
the same license:

* Zenuity AB
* Alina Boboc
* Benedikt Schmid

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
