% (c) Copyright 2019 Florian Schanda

% An undocumented extension to try ... catch is that the catch block
% is optional.

function baz()
    x = 5;
    y = 0;
    try
        z = x / y;
    end
end
