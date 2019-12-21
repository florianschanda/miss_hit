% (c) Copyright 2019 Florian Schanda

function test_01()
    kitten = 12;

    foo(kitten); % 12

    foo (kitten); % 12

    foo kitten; % kitten
    foo +kitten; % +kitten

    foo kitten ; % kitten
    foo +kitten ; % +kitten

    foo kitten % kitten
    foo +kitten % +kitten
end
