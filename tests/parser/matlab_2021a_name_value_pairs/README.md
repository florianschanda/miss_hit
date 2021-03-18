Tests for the new name-value misfeature that MATLAB introduced in
2021b.

This is a completely different approach to what every other language
does. Clearly the MATLAB language designers do not care about
interoperability and sanity, or indeed know about other languages, and
this is the perfect demonstration.

Normally something like `f(a=12)` would mean, the parameter called `a`
gets the value `12`. But no, in MATLAB this means `f('a', 12)` which
is just extremely dumb.

This is perfectly illustrated in `nv_pair_6.m` where we get *very*
different behaviours between MATLAB <2021a, >=2021a, and Octave.

FUCK.
