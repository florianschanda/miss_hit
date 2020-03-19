%% (c) Copyright 2020 Florian Schanda

function test_01
    persistent a
    persistent b
    if a > 0
        persistent c
    end
end
