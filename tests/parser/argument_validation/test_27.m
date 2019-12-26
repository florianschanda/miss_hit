% From https://www.mathworks.com/help/matlab/matlab_prog/function-argument-validation-1.html

c = test_26(1.8,1.5);
assert(c == 4);

c = test_26(1.8,1.5,25);
assert(c == 25);
