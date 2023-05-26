% Taken from https://uk.mathworks.com/help/matlab/matlab_oop/specifying-methods-and-functions.html

classdef Rectangle
    properties
        X (1,1) double {mustBeReal} = 0
        Y (1,1) double {mustBeReal} = 0
        Width (1,1) double {mustBeReal} = 0
        Height (1,1) double {mustBeReal} = 0
    end

    methods
        function R = enlarge(R,x,y)
            arguments (Input)
                R (1,1) Rectangle
                x (1,1) {mustBeNonnegative}
                y (1,1) {mustBeNonnegative}
            end
            arguments (Output)
                R (1,1) Rectangle
            end
            R.Width = R.Width + x;
            R.Height = R.Height + y;
        end
    end
end
