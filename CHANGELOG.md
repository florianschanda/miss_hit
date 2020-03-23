# MISS_HIT Release Notes

## 0.9.2-dev

* Workaround for #133 (multi-threading issues on windows)

### Known issues

#### Tooling

* #123 [formatting not always idempotent](https://github.com/florianschanda/miss_hit/issues/123)
* #133 [multi-threading on windows](https://github.com/florianschanda/miss_hit/issues/133)

#### Language support

* #88 [allow end as method name](https://github.com/florianschanda/miss_hit/issues/88)
* #131 [end of statement after enumeration optional](https://github.com/florianschanda/miss_hit/issues/131)

## 0.9.1

This is the first "release", previously it was all just one
development stream. This release contains two tools:

* mh_style.py: a fully functional style checker and code formatter for
  MATLAB.

* mh_metric.py: a mostly functional code metrics tool for MATLAB. Some
  metric (in particular cyclomatic complexity) are not measured yet.
