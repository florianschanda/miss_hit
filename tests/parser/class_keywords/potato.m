% (c) Copyright 2019 Florian Schanda

classdef potato
  properties
    x
    y
  end

  methods
    function r = foo(self)
      properties = x;
      r = properties;
    end
  end
end
