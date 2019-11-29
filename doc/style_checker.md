# Style Checker

`MISS_HIT` includes a simple style checker (mh_style.py). It can
detect and correct (when the `--fix` options given) a number of coding
style issues, some of which are configurable.

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

You can also specify the special `exclude_dir` property in
configuration files. This property must name a directory *directly
inside* (i.e. you can't specify `foo/bar`) the same directory the
configuration file resides in. This is especially useful when
including an external repository, over which we have limited control.

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

## Rules

There are three types of rules:

* Mandatory rules: they are always active and can be automatically fixed
* Autofix rules: they are optional and can be automatically fixed
* Rules: they are optional and cannot be automatically fixed

Rules with a name (for example `"whitespace_keywords"`) can be
individually suppressed in or re-enabled in configuration files. For
example:
```
suppress_rule: "operator_after_continuation"
suppress_rule: "builtin_shadow"
enable_rule: "file_length"
```
By default all rules are active.

### Mandatory rules

These rules are always active. The technical reason for this is that
it would be too difficult to autofix issues without autofixing
these. If you pay me an excessive amount of money I could look into
this but I'd rather keep the lexer vaguely sane. All of them are
automatically fixed by `mh_style.py` when the `--fix` option is
specified.

#### Consecutive blank lines

This rule allows a maximum of one blank line to separate code blocks.
Comments are not considered blank lines.

#### Trailing whitespace

This rule enforces that there is no trailing whitespace in your files.
You *really* want to do this, even if the MATLAB default editor makes
this really hard. The reason is that it minimises conflicts when using
modern version control systems.

#### Use of tab

This rule enforces the absence of the tabulation character
*everywhere*. When auto-fixing, a tab-width of 4 is used by default,
but this can be configured with the options `tab_width`.

Note that the fix replaces the tab everywhere, including in strings
literals. This means
```
"a<tab>b"
   "a<tab>b"
```
might be fixed to
```
"a        b"
   "a     b"
```

Which may or may not what you had intended originally. I am not sure
if this is a bug or a feature, but either way it would be *painful* to
change so I am going to leave this as is.


### Autofix rules

The following rules are automatically fixed by `mh_style.py` when the
`--fix` option is specified.

#### Whitespace surrounding commas ("whitespace_comma")

This rule enforces whitespace *after* commas, and no whitespace
*before* commas, e.g. `foo, bar, baz`.

#### Whitespace surrounding colon ("whitespace_colon")

This rule enforces no whitespace around colons, except after commas.

#### Whitespace around assignment ("whitespace_assignment")

This rule enforces whitespace around the assignment operation (=).

#### Whitespace surrounding brackets ("whitespace_brackets")

This rule enforces whitespace *after* square and round brackets, and
no whitespace *before* their closing counterpart.
For example: `[foo, bar]`

#### Whitespace after some words ("whitespace_keywords")

This rule makes sure there is whitespace after some words such as `if`
or `properties`.

#### Whitespace in comments ("whitespace_comments")

This rule makes sure there is some whitespace between the comment character
(%) and the rest of the comment. The exception is "divisor" comments like
`%%%%%%%%%%%%%%` and the special `%#codegen` comment.

#### Whitespace in comments ("whitespace_continuation")

This rule makes sure there is some whitespace between the last thing
on a line and a line continuation.


### Rules

These rules cannot be auto-fixed because there is no "obvious" fix.

#### Max lines in file ("file_length")

This is configurable with `file_length`, default is 1000. It is a good
idea to keep the length of your files under some limit since it forces
your project into avoiding the worst spaghetti code.

#### Max character per line ("line_length")

This is configurable with `line_length`, default is 80. It is a good
idea for readability to avoid overly long lines. This can help you
avoid extreme levels of nesting and avoids having to scroll around.

#### Copyright notice ("copyright_notice")

This rules looks for a copyright notice at the beginning of each file
in the form of `(C) Copyright YEAR-YEAR ENTITY` or 
`(C) Copyright YEAR ENTITY`.  The list of acceptable entities can be configured with
`copyright_entity`.  This option can be given more than once to permit
a set of valid copyright holders. If this options is not set, the rule
just looks for _any_ copyright notice.

#### Comma line endings ("eol_comma")

This rule complains about any line that ends in a comma. If you have
`;` at the end of each statement it really helps you pretend that your
using a real programming language, and so this rule is quite helpful
for sanity.

#### Shadowing of built-in functions ("builtin_shadow")

This rule attempts to find cases where we assign to a MATLAB builtin
function (e.g. `false = 0.1`). This rule does not catch all cases,
once we have a parse this can be done easily.
