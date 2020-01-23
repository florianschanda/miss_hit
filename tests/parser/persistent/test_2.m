% From https://uk.mathworks.com/help/matlab/ref/persistent.html

function logData(fname,n)
    persistent logTime
    currTime = datetime;

    if isempty(logTime)
        logTime = currTime;
        disp('Logging initial value.');
        dlmwrite(fname,n);
        return
    end

    dt = currTime - logTime;
    if dt > seconds(3)
        disp('Logging.');
        dlmwrite(fname,n,'-append');
        logTime = currTime;
    else
        disp(['Not logging. ' num2str(seconds(dt)) ' sec since last log.']);
    end
end
