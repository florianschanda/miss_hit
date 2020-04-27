% (c) Copyright 2020 Florian Schanda

classdef cls

    % Turns out *some* keywords go too far, even for MATLAB. Why those and
    % not others seems arbitrary.

    methods
        %function x = break(self)
        %    x = 1;
        %end

        %function x = case(self)
        %    x = 2;
        %end

        %function x = catch(self)
        %    x = 3;
        %end

        %function x = classdef(self)
        %    x = 4;
        %end

        %function x = continue(self)
        %    x = 5;
        %end

        %function x = else(self)
        %    x = 6;
        %end

        %function x = elseif(self)
        %    x = 7;
        %end

        function x = end(self)
            x = 8;
        end

        %function x = for(self)
        %    x = 9;
        %end

        %function x = function(self)
        %    x = 10;
        %end

        %function x = global(self)
        %    x = 11;
        %end

        %function x = if(self)
        %    x = 12;
        %end

        %function x = otherwise(self)
        %    x = 13;
        %end

        %function x = parfor(self)
        %    x = 14;
        %end

        %function x = persistent(self)
        %    x = 15;
        %end

        %function x = return(self)
        %    x = 16;
        %end

        %function x = spmd(self)
        %    x = 17;
        %end

        %function x = switch(self)
        %    x = 18;
        %end

        %function x = try(self)
        %    x = 19;
        %end

        %function x = while(self)
        %    x = 20;
        %end

        function x = import(self)
            x = 21;
        end

        function x = methods(self)
            x = 22;
        end

        function x = properties(self)
            x = 23;
        end

        function x = events(self)
            x = 24;
        end

        function x = enumeration(self)
            x = 25;
        end

        function x = arguments(self)
            x = 26;
        end

        function x = wibble.wabble(self)
            x = 27;
        end
    end

end
