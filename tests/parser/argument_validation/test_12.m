% From https://www.mathworks.com/help/matlab/matlab_prog/function-argument-validation-1.html

function test_12(x,y)
    arguments(Repeating)
        x (1,:) double
        y (1,:) double
    end

    % Function code
    % Interleave x and y
    z = reshape([x;y],1,[]);

    % Call plot function
    if ~isempty(z)
        plot(z{:});
    end
end
