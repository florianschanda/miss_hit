% Extracted from the Octave tests parser.tst
function basic()
    % all of these should be {1,2,{3,4}}
    x = {1 2 {3 4}}
    x = {1, 2 {3 4}}
    x = {1 2, {3 4}}
    x = {1 2 {3, 4}}
    x = {1, 2, {3 4}}
    x = {1 2,{3 4}}
    x = {1 2,{3,4}}
    x = {1,2,{3 4}}
end
