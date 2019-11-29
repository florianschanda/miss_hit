# Style Checker

`MISS_HIT` includes a simple style checker (mh_style.py). It can
detect and correct (when the `--fix` options given) a number of coding
style issues, some of which are configurable.

## Features

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

* (autofix) Whitespace surrounding commas

* (autofix) No whitespace after opening brackets '(' or '[', and no
  whitespace before closing brackets ')' or ']'

* (autofix) Whitespace after certain words such as 'if' or 'properties'.

* (autofix) Use of tab anywhere (adjust with `--tab-width`)

* (autofix) Whitespace after the comment indicator % or #, and before
  the body of the comment.

* (autofix) Whitespace before comments or continuations.

* (autofix) No whitespace around colon (except for after a comma)

* Assigning to builtin functions, such as false.

* Ending a line with a comma

* Line continuations should not start with an operator of any kind.

## Configuration files

Options are read from configuration files `miss_hit.cfg`. (This
behaviour can be disabled with the `--ignore-config` option). When
analysing the file `foo/bar/potato.m`, we will first look in the root
for `miss_hit.cfg`, then in `foo/miss_hit.cfg`, and finally in
`foo/bar/miss_hit.cfg`. Each file augments/overwrites previously given
configuration, and command-line options overwrite everything.

For example you can put this `miss_hit.cfg` in your project root:

```
# Options written like on the commandline, but with _ instead of -
line_length: 100
file_length: 2500
copyright_entity: "Lord Buckethead"
```

And you can adjust options in subdirectories, for example if you place
this in `foo/miss_hit.cfg`:

```
# Legacy code which had a different coding standard
line_length: 180
```

Then files in `foo/` or below will be checked for a line length of 180
(redefined) and a file length of 2500 (taken over from the project
root).

## Excluding files from analysis

A special entry `enable` into a `miss_hit.cfg` can be used to enable
or disable analysis for the subtree.

For example if you have a lot of legacy code you can put this into
your root configuration:

```
enable: 0
line_length: 100
```

And then enable analysis for some subdirectories, e.g. in
`foo/new_code/miss_hit.cfg` you can write:

```
enable: 1
```

Like any other option, the "closest one" takes precedence.

## Permanently excluding subtrees from analysis

You can also specify the special `exclude_dir` property in
configuration files. This property must name a directory *directly
inside* (i.e. you can't specify `foo/bar`) the same directory the
configuration file resides in. This permanently excludes the entire
subtree from analysis, i.e. it cannot be overwritten again with
`enable: 1`. This is especially useful when including an external
repository, over which we have limited control.

Below is given a more realistic root configuration:
```
file_length: 1000
line_length: 120
copyright_entity: "Potato Inc."

% We include the delightful miss_hit tools in our repo, but don't want to
% accidentally check their weird test cases
exclude_dir: "miss_hit"
```

## Justifications

Style issues can be justified by placing `mh:ignore_style` into a
comment or line continuation. The justification applies to all style
issues on that line.

Justifications that are useless generate a warning.
