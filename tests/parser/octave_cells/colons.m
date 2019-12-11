% Extracted from the Octave tests parser.tst
function colons()
    z = cell (1,2,3,0,5);
    assert ({1, z{:}, 2} == {1, 2});
    assert ({1; z{:}; 2} == {1; 2});
    assert ({1 2; z{:}; 3 4} == {1, 2; 3 4});
    assert ({1 2; 5 z{:} 6; 3 4} == {1, 2; 5 6; 3 4});
end
