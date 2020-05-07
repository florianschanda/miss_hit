% (c) Copyright 2020 Zenuity AB

classdef Potato

    properties
        value (1, 1) logical
    end

    methods
        function obj = Potato(val)
            obj.value = val;
        end

        function result = logical(obj)
            result = obj.value;
        end

        function result = and(lhs, rhs)
            disp("potato");
            result = lhs.value & rhs.value;
        end
    end

end
