% (c) Copyright 2020 Florian Schanda

function maybe_exception

    if rand() > 0.5
        throw(MException('MH:test', 'this is a test exception'));
    end

end
