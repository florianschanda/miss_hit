% (c) Copyright 2021 Florian Schanda

classdef Test_1

    enumeration
        foo  % no
        Bar  % ok
    end

    enumeration
        BAZ         % ok
        Bork_Class  % ok
    end

    enumeration
        wrong5  % no
    end

end
