%% (c) Copyright 2020 Florian Schanda

function function_file
  if rand() > 0.5
    %| pragma Justify(metric, "npath", "(invalid, does not apply)");
    disp heads;
  else
    disp tails;
  end

  if rand() > 0.5
    disp heads;
  else
    disp tails;
  end

  if rand() > 0.5
    disp heads;
  else
    disp tails;
  end
end

%| pragma Justify(metric, "npath", "(invalid, does not apply)");
