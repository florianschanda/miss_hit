% (c) Copyright 2019 Zenuity AB

function lexing_issues()
    x = 10;
    a = {(x) 2};    % {x, 2}
    b = {@(x) 2};   % {@(x)2}
    c = {@ (x) 2};  % {@(x)2}
    d = {@ (x)2};   % {@(x)2}

    e = {@(x) x + 1}; % {@(x)(x+1)}
    f = {@(x) x+ 1};  % {@(x)(x+1)}
    g = {@(x) x +1};  % {@(x)x, 1}
    h = {@(x) x+1};   % {@(x)(x+1)}
end
