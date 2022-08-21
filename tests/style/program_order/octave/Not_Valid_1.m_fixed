% (c) Copyright 2021 Florian Schanda

function rv = Not_Valid_1 (x)
    persistent z
    if isempty(z)
        global y
        z = y;
    end

    rv = x + z;
    z = z + 1;

end
