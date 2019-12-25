% From the Octave testsuite, complex.tst and parser.tst

x = [0 i 1+i 2 3i 3+4i];
x = [1, -1, i, -i];
x = i;
assert (3*4i'.', 0 - 12i);
assert (3*4i.'.', 0 + 12i);
