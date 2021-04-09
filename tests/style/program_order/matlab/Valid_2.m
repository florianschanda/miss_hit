% (c) Copyright 2021 Florian Schanda

function rv = Valid_2 (x)
    arguments
        x uint32
    end

    persistent z
    global y

    if isempty(z)
        z = 0;
    end

    rv = x + y + z;
    z = z + 1;

end
