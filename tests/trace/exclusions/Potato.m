% (c) Copyright 2021 Florian Schanda

classdef Potato

    methods
        function x = method_a()
            %| pragma Tag ("OK");
            x = 0;
        end

        function x = method_b()
            %| pragma No_Tracing;
            %| pragma Tag ("Not OK");
            x = 0;
        end
    end

end
