% (c) Copyright 2020 Florian Schanda

classdef Class_B
    methods

        function obj = Class_B()
            Potato(); % not visible, so gives an error
        end

        wibble(self, x)

    end
end
