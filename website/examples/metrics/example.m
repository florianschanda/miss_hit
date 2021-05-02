function rv = example (a, b)
  if a < b
    rv = -1;
  elseif a > b
    rv = 1;
  else
    rv = 0;
  end

  if a > 5
    rv = 2;
  end

  if b > 5
    rv = local_function (b);
  end
end

function rv = local_function (a)
  %| pragma Justify(metric, "npath", "this cannot be reasonably refactored");
  if a > 1
    rv = 1;
  end
  if a > 2
    rv = 2;
    if a > 3
      rv = 3;
    end
    if a > 4
      rv = 4;
    end
  end
end
