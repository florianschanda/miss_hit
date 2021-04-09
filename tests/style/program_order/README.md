Tests for a new rule, to make sure function bodies follow this
pattern:

1. Argument validation blocks (only in matlab 2019b)
2. imports
3. global | persistent (in either order, as long as they are grouped)
4. function body
5. nested functions

In MATLAB, rules 1 and 5 are a hard language requirement.
In Octave, rules 1 is not applicable, but rule 5 should be checked.

This testsuite is only for MATLAB.
