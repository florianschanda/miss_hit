% (c) Copyright 2021 Florian Schanda

function rv = Valid_5 (x)
    persistent z

    if isempty(z)
        z = 0;
    end

    rv = x + z;
    z = z + 1;

end
