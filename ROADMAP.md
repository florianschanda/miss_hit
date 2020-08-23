# MISS_HIT Road map

This project is a labour of love (or hate, the two have been remarked
on being sufficiently similar by many philosophers). Progress will not
be amazingly fast. Things I intend to publish, not necessarily in this
order:

* A data-flow analysis tool to detect e.g. unused or uninitalised
  variables.

* Support for Simulink and Stateflow complexity metrics.

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

* A code generator (intended targets are C, C++, and SPARK) that
  precisely follows the documented semi-formal semantics.

* A VC generation tool (either under-approximate BMC or deductive). To
  be decided later.

* A qualification pack that maps the semi-formal semantics we decided
  to any specific MATLAB (R) version, demonstrating that the semantics
  are precisely correct or a safe over-approximation.
