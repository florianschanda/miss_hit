% From https://www.mathworks.com/help/matlab/matlab_prog/function-argument-validation-1.html

function test_19(x,y,scale)
    arguments(Repeating)
        x (1,:) double
        y (1,:) double
    end
    arguments
        scale.PlotType (1,1) string
    end
    z = reshape([x;y],1,[]);
    if isfield(scale,"PlotType")
        if scale.PlotType == "lin"
            plot(z{:})
        elseif scale.PlotType =="log"
            loglog(z{:})
        end
    end
end
