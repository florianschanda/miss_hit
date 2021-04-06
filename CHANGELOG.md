# MISS_HIT Release Notes

## Known issues

### Language support

Compatible with up to MATLAB 2021a.

Not quite compatible with Octave yet. See #43 [octave support](https://github.com/florianschanda/miss_hit/issues/43) for more information.

### Tooling

* In some cases MH Style will not fix everything in one run, and it
  may be necessary to run the tool more than once. Issues like these
  will be resolved with the planned MH Reformat tool, and will not be
  fixed in MH Style.

## Changelog

### 0.9.18

* Completely new handling of copyright notices. New configuration
  option `copyright_location` decides which approach to use. It can
  take one of the following values:
  * `docstring` - the new (and default) approach, copyright notice
    must be somewhere in the docstring of the class, function, or
    script file; or at the top of the file.
  * `file_header` - similar (but not identical) to the old behaviour,
    copyright notice must be in the file header. However the tool is a
    bit more relaxed where the copyright notice can appear, and it no
    longer must be the first line in the file.

  Please note that this changes the *default* behaviour, if you like
  something closer to the old approach use `file_header`. The
  intention however is to make it possible to write sensible
  docstrings for working with the MATLAB/Octave help functions; and
  this new default achieves this.

  Your current notices, if they exist, should be compatible with the
  new default. Except that we now process and check all notices, not
  just the first one.

* The MH Copyright tool has been updated to deal with docstrings as
  well. It is unfortunately slower (because it now has to parse the
  file).

* New rule for MH Style `naming_scripts` and associated configuration
  option `regex_script_name`. The existing naming rules cover all
  functions, classes and methods. However script escaped this because
  they are _not_ functions as such. The default for this is the Ada
  naming scheme (the same default as we have for functions and
  classes).

* Fix oversight in MH Lint for checking built-in shadows. Now files
  (scripts, functions, and classes) are correctly considered. This
  check uses a much broader list of built-in functions, than the check
  that looks at assignments.

* New check for MH Lint to make sure that any file called `Contents.m`
  only contains comments.

* Fixed an obscure internal issue in the lexer: the opening `%{` of a
  block comment now correctly has the block_comment flag set, and the
  closing marker `%}` now has the correct value of `}` instead of
  `%}`. There is no user-visible change, but any direct users of the
  lexer that relied on the old broken behaviour need to remove their
  workarounds.

* MISS_HIT is now also published on the
  [MathWorks "File Exchange"](https://www.mathworks.com/matlabcentral/fileexchange/89436-miss_hit).

  From now on, the tags will be just the version number, and not
  prepended with `release-`. For example the tag for this release is
  `0.9.18` (and not `release-0.9.18`). The reason for this is that the
  automatic sync with the MathWorks "File Exchange" only works if the
  release numbers are following the MAJOR.MINOR.PATCH pattern.

### 0.9.17

* Updated language support to MATLAB 2021a. The new feature supported
  is the new (and extremely unwise) function name-value pairs. This
  allows you to write `foo(bar=baz)` instead of two separate
  arguments: `foo('bar', baz)`. Note very carfully that this is
  totally different to all other programming languages out there, and
  not what any reasonable person expects.

  Further note that Octave actually does something worse here, in
  Octave this would be a side-effect assinment to bar, and only a
  single argument would be passed.

* MH Lint has a new (low) check for discouraging the use of name-value
  function arguments.

* Fix wrapper class (`miss_hit.m`), I forgot to update the file names
  when I remove the `.py` from the main entry points.

### 0.9.16

* New tool [MH Copyright](https://florianschanda.github.io/miss_hit/copyright.html)
  to update and change copyright notices in your projects. This can
  perform one of four actions:
  * update years
  * replace one entity with another
  * merge multiple entities into one
  * add missing notices to files without one

* New configuration options for the `copyright_notice` rule of MH
  Style. You can now change the magic regex to detect copyright
  notices (`copyright_regex`), and add 3rd party copyright holders
  (`copyright_3rd_party_entity`), and indicate a key copyright holder
  (`copyright_primary_entity`). These options are also considered by
  the MH Copyright tool.

* Fix issue with entry points: private directories were ignored, they
  are now considered correctly.

* Fix issue in MH Style for name checking class methods: class
  constructors should obviously follow the class naming scheme, not
  the method naming scheme.

* Fix issue in MH Style where some confusing messages relating to
  indentation would be emitted if there was a parse error in the file.

* Fix bug in all tools relating to `copyright_entity`. These could
  be unexpectedly shared between different directory trees, this is
  now fixed and is working as documented.

* Support Octave script-global functions in `--octave` mode. These are
  function definitions that are sprinkled in the middle of a script
  file, instead of appearing at the end. Also vastly improve the error
  message that appears when encountering this construct in MATLAB
  mode.

### 0.9.15

* Added [documentation](https://florianschanda.github.io/miss_hit/configuration.html#pre-commit) on how to use MISS_HIT through pre-commit hooks.

* Libraries can now be declared `global`, making them a dependency for
  all other libraries and entry points. This is useful for larger
  code-bases with shared code among all components (e.g. interface
  definitions).

* MH Style has a new rule `whitespace_around_functions` that makes
  sure each function, nested function, or class method is separated by
  one blank line from surrounding context. This also works for
  function without an explicit `end` keyword.

* MH Lint has a new check to make sure the filename of a function or
  class files match the function or class name declared within.

* Fixed bug in MH Style where blank lines after annotations
  (e.g. `pragma Justify`) could sometimes be deleted.

### 0.9.14

* Support for [projects](https://florianschanda.github.io/miss_hit/configuration.html#shared-code).
  This is a major new feature for all MISS_HIT tools, intended to make it
  easier to analyse specific programs in large shared code repositories.
  For example instead of having to do:
  ```
  $ mh_lint shared_lib_1 shared_lib_2 my_potato_app my_potato_lib
  ```
  You can now instead simply do:
  ```
  $ mh_lint --entry-point=PotatoApp
  ```

  You can set up libraries and entrypoints and the dependencies
  between them with new [configuration directives](https://florianschanda.github.io/miss_hit/configuration.html#projects).

  Currently the functionality is limited, however in the future this
  will be the basis for all advanced static analysis; since it
  provides the equivalent of path or matlabpath to the MISS_HIT tools.

* New documentation for the
  [common command-line interface](https://florianschanda.github.io/miss_hit/cli.html), which is shared between all MISS_HIT tools (except for MH Diff).

* New switch for all tools `--input-encoding` (which is by default
  cp1252). You can use this to request a different input encoding to
  be used when reading files.

  Note: this is not applicable for Simulink models, since Simulink
  models actually specify the input encoding to be used.

* MH Style has a new rule `unicode` and two new configuration options
  `enforce_encoding` and `enforce_encoding_comments` to make sure
  source files only contain ASCII characters.

  You can configure the encoding enforced using `enforce_encoding` to
  e.g. `iso8859_15`, if that is what you want instead; and you can
  optionally allow comments and line continuations to contain
  anything.

* Fixed bug in MH Metric HTML reports. When MH Metric was installed
  via pip, the link to the assets and stylesheetds did not
  resolve. This is now fixed.

  In addition the new `--portable-html` option for MH Metric will
  hotlink to the assets from https://florianschanda.github.io/miss_hit
  instead of trying to use the ones from the locally installed
  MISS_HIT.


### 0.9.13

* All tools can now run without parameters. By default we analyse the
  current directory, i.e. the default behaviour of `mh_style` is now
  the same as `mh_style .`

* [MH Diff](https://florianschanda.github.io/miss_hit/diff.html):
  A new tool, that can be used to diff the code embedded
  inside Simulink models. The best way to use it is through `git`, for
  example: `git difftool HEAD^ -yx "mh_diff" Potato.slx`

  You can also provide the option `--kdiff3` to show a visual diff (on
  systems that have `kdiff3` installed).

* Config file directive no longer _have_ to be separated by
  newlines. While this is still encouraged for readability, it is no
  longer an error to write a single directive over multiple lines or
  multiple directives on the same line.

* Fix minor issue with `regex_tickets` where regular expressions with
  brackets only matched what was inside the brackets. For example a
  ticket regex with `(a|b)-[0-9]` should match both `a-5` and `b-2`,
  but the ticket mentioned in the report was only `a` and `b`.

* Support hex and binary literals (e.g. `0x12s64`) from MATLAB
  2019b. This resolves the one outstanding compatibility issue, and we
  should now be compatible with up to and including MATLAB 2020b.

* MH Style now accepts a slightly wider form of copyright statements
  (specifically you can now include the word 'by' before the legal
  entity).

### 0.9.12

* [*CORRECTNESS*] Fix lexing of `1./b`. This was a critical bug that
  caused the expression to be incorrectly formatted as `1. / b`
  (i.e. using `/` instead of `./`).

  The main user-visible problem is that the style rule
  `operator_whitespace` could then re-write expressions and change
  semantics of the re-written code.

* Fix parsing of `[,]`. This is a valid expression and is equivalent
  to `[]`. Previously a syntax error was issued.

* Fix parsing of `[;;1]` and similar expressions where leading or
  trailing semicolons or newlines were present in a matrix or
  cell. Previously a syntax error was issued.

* MH Style has a new rule `spurious_row_semicolon` which removes
  useless semicolons from matrix or cell expressions.

* MH Style now aligns any continuations in a more sensible way if the
  expression is inside brackets. This works for normal brackets, but
  also matrix and cell expressions:
  ```
  potato = [1 0
            0 1];
  kitten = foo(bar, ...
               baz);
  ```

  There are two new configuration options to control this behaviour:
  `align_round_brackets` and `align_other_brackets` for `(` and `[{`
  respectively.

* New configuration option `regex_tickets` which can be used to
  identify which text strings are tickets in your particular issue
  tracking system. This information is used by MH Metric to produce a
  report on all tickets referenced in justifications.

* [MH BMC](https://florianschanda.github.io/miss_hit/bmc.html):
  Started work on an experimental tool for bounded model
  checking. This tool is not usable for anything yet, but is intended
  as a proof-of-concept.

* Also provide the `--html` option for MH Lint.

* New `--json` option for MH Style and MH Lint to produce message
  using JSON. In the future the `--html` option from MH Style and MH
  Lint will disappear and be replaced by a small set of tools that
  render JSON messages in plain text, HTML, or post messages as gerrit
  review comments. The exact schema of this JSON file is not stable
  yet.

### 0.9.11

* MH Lint now contains the three lint-like messages that were part of
  MH Style previously (block comments, relation chaining, and builtin
  redefinition). MH Style no longer issues these messages.

  Note that MH Lint currently operators on a file-by-file basis like,
  just like the other MISS_HIT tools. However this will definitely
  change in the future, as we move to a "per project" analysis for the
  linter. But for now MH Lint can be use just like the other tools.

* The configuration directive "style rule" for "builtin_redefinition"
  is now a lint rule; while this change is not documented yet properly
  it will mean existing configuration files continue to work. I have
  not yet decided how lint rules will be configurable, but it is
  likely they will share a namespace with the style rules.

* Added documentation for lint checks, explaining the meaning of
  "low", "medium", and "high" checks.

* Added [GitHub and Travis CI templates](https://florianschanda.github.io/miss_hit/configuration.html#cicd) to the documentation. Thank you Remi Gau for your contribution.

* MH Style now correctly vertically aligns annotations. One-line
  annotation blocks were always OK, but multi-line annotations were
  considered continuations (and thus indented in an unnatural way).

* MH Style has a new rule `spurious_row_comma` which complains about
  trailing or starting commas in matrix and cell expressions (for
  example: `[,1,2,]`)

* MH Style has a new rule `whitespace_semicolon` which does the same
  as `whitespace_comma`, but for semicolons; this means one-line
  matrix expressions are now nicely formatted.

* MH Style should now only print `[fixed]` for problems that really
  are fixed. Specifically in files that contain parse errors, we now
  no longer pretend the problems are fixed.

* Fixed an issue for all MISS_HIT tools where any issue in embedded
  MATLAB code could be reported multiple times.

### 0.9.10

* Fixed another Windows multi-threading issue.

* Reverted new behaviour to consider all directories containing `.git`
  as a project root. It is useful, but until it can be configured
  ([#156](https://github.com/florianschanda/miss_hit/issues/156)) it can
  be really disruptive.

* MH Metric can now produce reports in JSON using the new `--json`
  option.

* Rename packages (`miss_hit_agpl` is now `miss_hit`, and `miss_hit`
  is now `miss_hit_core`). It's likely this is not the last renaming,
  sorry. I can only promise that it will be stable after 1.0 is
  released.

### 0.9.9

* Minor fix for the case where an excluded_dir contains a broken
  config file.

### 0.9.8

* #151 Rewrote configuration file mechanism. The change is backwards
  compatible, so existing files will continue to work.
  * Fixed an issue where broken configuration files higher up the
    directory tree (and unrelated to the project you're analysing)
	impacted analysis.
  * Fixed an issue where files in directories hard-excluded (i.e. using
    `exclude_dir` as opposed to `enable: 0`) counted as files excluded
	from analysis. This seems weird, but the intention was that excluded
	directories were effectively considered deleted and would not influence
	anything, ever.
  * We no longer enter any directory starting with `.` when searching for
    files to analyse.
  * New config directive `project_root` that effectively resets all
    configuration and starts from a blank slate.
  * Any directory containing the `.git` directory is also considered a project
    root. This means checkout out sub-projects are not influenced by your
	configuration file. I plan to make this behaviour configurable in the
	future.
  * Proper [documentation for configuration files](https://florianschanda.github.io/miss_hit/configuration.html)

### 0.9.7

* #148 MISS_HIT is now a PyPI package. This change should also make
  it much easier to re-use the compiler framework of MISS_HIT in other
  tools.  You can still use it by just checking out the code, but be
  aware that some entry points have changed:
  * most source code lives in the miss_hit package (not the top-level)
  * the top-level script `mh_metric.py` is now called `mh_metric`
  * the top-level script `mh_style.py` is now called `mh_style`

* Reworked Simulink parser to provide a much deeper parsing. While
  there is no user-visible effect of this change right now, it paves
  the way for producing code metrics on the Simulink model itself (and
  not just embedded MATLAB code).

### 0.9.6

* MH Style can now analyse (and fix) code inside Simulink models. This
  new functionality must be enabled with the new command-line flag
  `--process-slx`. This flag is temporary and will be removed in the
  future once this feature is stable enough.

* MH Style has a new configuration option `copyright_in_embedded_code`
  which is turned off by default. By default the `copyright_notice`
  rule does not apply to embedded code, and this option can be used to
  control that behaviour.

* MH Style has a wider definition of a `useless_continuation`. This
  rule now also applies to continuations that begin statements.

* MH Metric has a new syntax in configuration files to completely
  disable a named software metric. You do this with `disable` for a
  named metric, e.g. `metric "function_length": disable`. With this
  option the metric doesn't even appear in the final report (as
  opposed to the default where we measure a metric, but not complain
  about it).

* MH Metric has new syntax in configuration files to enable or disable
  all metrics. You do this by using `metric *: report` and
  `metric *: disable` respectively.

* MH Metric now uses more human readable names for the metrics in both
  the HTML and text report.

### 0.9.5

* Disabled (but not removed) the `implicit_shortcircuit` rule. It
  turns out that in some cases `&` really does mean `&`, even inside
  an if guard. Curiously, mlint/checkcode shares this bug. To properly
  resolve this we need semantic analysis and type inference; so until
  then this rule just does nothing.

* MH Metric can now process and produce metrics for code inside modern
  SIMULINK models (slx files). This does not work yet in MH Style, but
  I plan to also support this there.

### 0.9.4

#### Features
* MH Style has a new (autofixed) rule `no_starting_newline` to make
  sure files do not start with just whitespace.

* MH Style has a new (autofixed) rule `implicit_shortcircuit` that
  complains about misleading use of `&` and `|` inside if/while
  guards.

* The MH tools now allow all possible class method names, even the
  ones that are highly questionable like "import", "end", or
  "arguments".

#### Fixes
* #131 The parser now allows the end of statement (newline, comma, or
  semicolon) after an enumeration keyword to be optional. I.e. we can
  now process this code fragment correctly:

  ```
  enumeration Picasso, Laura, King_Edward
  end
  ```

### 0.9.3

#### Features
* MH Metric can now measure cyclomatic complexity. We've aimed for
  producing the same numbers as mlint does, even if it's wrong.

* MH Metric produces an (optional) table of "worst offenders" for each
  metric. This can be used to get a quick overview of code smell.

#### Fixes
* Fix for #133: resolved multi-threading issues on Windows. To be
  honest, this seems more like a Python bug.

### 0.9.2

#### Fixes
* Workaround for #133. Until I can work what the root cause of this
  is, multi-threading is disabled on Windows platforms.

### 0.9.1

This is the first "release", previously it was all just one
development stream. This release contains two tools:

* mh_style.py: a fully functional style checker and code formatter for
  MATLAB.

* mh_metric.py: a mostly functional code metrics tool for MATLAB. Some
  metric (in particular cyclomatic complexity) are not measured yet.
