% From https://uk.mathworks.com/help/matlab/matlab_oop/calling-superclass-methods-on-subclass-objects.html

classdef subclass < MySuperClass
    methods
        function obj = MySub(arg1,arg2)
            obj = obj@MySuperClass(SuperClassArguments);
        end

        function disp(obj)
            disp@MySuperClass(obj);
        end
    end
end
