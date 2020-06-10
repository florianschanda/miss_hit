% (c) Copyright 2020 Florian Schanda

% Before #142 was fixed, the code would be auto-fixed to
% this. Included here to make sure we also fix this to something sane.

classdef Potato2

    properties
        foo
        ...
          bar (1, 1)
        ...
          baz = 5
        ...
          bork single
    end

end
