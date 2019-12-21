% (c) Copyright 2019 Florian Schanda

function invalid_03()
    kitten = 12;
    foo + kitten; % semantic error (foo is function and missing input)
end
