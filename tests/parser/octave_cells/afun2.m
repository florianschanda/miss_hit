% Extracted from the Octave tests parser.tst
function afun2()
    a = {1, @sin, 2, @cos};
    b = {1 @sin 2 @cos};
    assert (a == b);
end
