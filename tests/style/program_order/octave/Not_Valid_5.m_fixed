% (c) Copyright 2021 Florian Schanda

function rv = Not_Valid_5 (x)
    persistent y

    if isempty(y)
        y = 0;
    end

    persistent z

    if isempty(z)
        z = 0;
    end

    rv = x + z;
    z = z + 1;
end
