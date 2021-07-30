% (c) Copyright 2021 Florian Schanda

function foo

    _x = _potato(5);
    disp(_x);

    function _rv = _potato(_input)
        _rv = _input + 1;
    end

end