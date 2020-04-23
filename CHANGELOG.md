# MISS_HIT Release Notes

## 0.9.4-dev

* MH Style has a new rule `no_starting_newline` to make sure files do
  not start with just whitespace.

### Known issues

#### Tooling

* #123 [formatting not always idempotent](https://github.com/florianschanda/miss_hit/issues/123)

#### Language support

* #88 [allow end as method name](https://github.com/florianschanda/miss_hit/issues/88)
* #131 [end of statement after enumeration optional](https://github.com/florianschanda/miss_hit/issues/131)

## 0.9.3

* MH Metric can now measure cyclomatic complexity. We've aimed for
  producing the same numbers as mlint does, even if it's wrong.

* MH Metric produces an (optional) table of "worst offenders" for each
  metric. This can be used to get a quick overview of code smell.

* Fix for #133: resolved multi-threading issues on Windows. To be
  honest, this seems more like a Python bug.

## 0.9.2

* Workaround for #133. Until I can work what the root cause of this
  is, multi-threading is disabled on Windows platforms.

## 0.9.1

This is the first "release", previously it was all just one
development stream. This release contains two tools:

* mh_style.py: a fully functional style checker and code formatter for
  MATLAB.

* mh_metric.py: a mostly functional code metrics tool for MATLAB. Some
  metric (in particular cyclomatic complexity) are not measured yet.
