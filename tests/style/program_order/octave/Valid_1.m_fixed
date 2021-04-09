% (c) Copyright 2021 Florian Schanda

function rv = Valid_1 (x)
    arguments
        x uint32
    end

    global y
    persistent z

    if isempty(z)
        z = 0;
    end

    rv = x + y + z;
    z = z + 1;

end
