% (c) Copyright 2021 Florian Schanda

%| pragma Tag("potato");

function x = bar()
    %| pragma Tag("kitten");
    x = inner(5);

    function y = inner(z)
        %| pragma Tag("wibble");
        y = z + 1;
    end

end
