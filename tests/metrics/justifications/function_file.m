%% (c) Copyright 2020 Florian Schanda

function function_file
  if rand() > 0.5
    % mh:metric justify npath: (invalid, does not apply)
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

% mh:metric justify npath: (invalid, does not apply)
