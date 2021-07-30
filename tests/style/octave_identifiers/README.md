The grammar for Octave and MATLAB identifiers is almost equal. Almost.

https://www.mathworks.com/help/matlab/ref/isvarname.html

> A valid variable name begins with a letter and contains not more
> than namelengthmax characters. Valid variable names can include
> letters, digits, and underscores. MATLAB keywords are not valid
> variable names. To determine if the input is a MATLAB keyword, use
> the iskeyword function.

https://octave.org/doc/v6.3.0/Variables.html#Variables

> The name of a variable must be a sequence of letters, digits and
> underscores, but it may not begin with a digit.

Specifically this means `_x` is OK in Octave, but not OK in MATLAB.
