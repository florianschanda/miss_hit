% (c) Copyright 2021 Florian Schanda

function rv = Not_Valid_2 (x)
    arguments
        x uint32
    end

    persistent z
    global y
    persistent w

    if isempty(z)
        z = 0;
        w = 0;
    end

    rv = x + y + z;
    z = z + 1;

end
