# MISS_HIT Road map

This project is a labour of love (or hate, the two have been remarked
on being sufficiently similar by many philosophers). Progress will not
be amazingly fast.

There are some tools and features that I want to work on:

* A data-flow analysis tool to detect e.g. unused or uninitalised
  variables. This will be part of MH Lint.

* Support for Simulink and Stateflow complexity metrics. This will be
  part of MH Metric.

* A code generator (intended targets are C, C++, and SPARK) that
  precisely follows the documented semi-formal semantics. This will be
  a new tool.

* A deductive verification tool. This tool will most likely be called
  MH Verify.

* A bounded model checker; a tiny amount of work on this has
  started. The tool will be called MH BMC.

* A diff tool for Simulink. Work on this has started, the tool will be
  called MH Diff.

* A semantic diff tool; intended to speed up CI activities so you can
  avoid e.g. generating code if you only made some simple
  comment/config changes. I might do this in MH Diff, or provide a
  separate tool.

* A portability checker. You can provide a set of language dialects
  (e.g. MATLAB 2017a, 2020b, Octave 4.4.1) and the tool will tell you
  if the program is means the _same thing_ in all. It might also be
  able to auto-fix some issues (e.g. converting octave double quoted
  character arrays into single quoted character arrays).

Other things I intend to publish, not necessarily in this order:

* A formal grammar for the language accepted by MATLAB (R) or Octave.

* A language subset called MISS_HIT. The MATLAB (R) code generator
  requires a subset anyway, so most people are used to the idea of
  subsets already. This language subset will be the basis of the
  static analysis that is planned.

* Safe semi-formal semantics for the MISS_HIT subset, which may not be
  the officially correct ones, but which should over-approximate the
  real ones. This means that they may be much stricter than what you
  might be able to do, but if the tool indicates it's safe here then
  it's safe for real too.

* A qualification pack that maps the semi-formal semantics we decided
  to any specific MATLAB (R) version, demonstrating that the semantics
  are precisely correct or a safe over-approximation.
