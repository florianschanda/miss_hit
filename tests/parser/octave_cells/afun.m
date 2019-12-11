% Extracted from the Octave tests parser.tst
function afun()
    af_in_cell = {@(x) [1 2]};
    assert (af_in_cell{1}() == [1, 2]);
end
