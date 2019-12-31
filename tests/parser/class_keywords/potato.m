% (c) Copyright 2019 Florian Schanda

classdef potato
  properties
    x
    y
  end

  methods
    % allowed
    function r = foo(self)
      properties = x;
      r = properties;
    end
    
    % allowed but idiotic
    function p = properties(self)
        p = 123;
    end
  end
end
