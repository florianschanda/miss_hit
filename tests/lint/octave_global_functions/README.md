Octave has very confusing semantics when it comes to functions in
*script* files. These are made globally available, as if they were in
their own `m` file; but only if the script is run first.
