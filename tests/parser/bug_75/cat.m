% (c) Copyright 2020 Florian Schanda
classdef cat < potato.kitten
    methods
        function meow(self)
            % calls superclass meow, but uses a dotted name
            self.meow@potato.kitten;
            disp("*destory stuff*");
        end
    end
end
