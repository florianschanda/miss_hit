function sequence
    x = 1;
    y = 2;
end

function ifs (x)
    if x
      a = 1;
    end
    if x
      b = 2;
    end
    if x
      c = 2;
    end
end

function loops_1
  for x = 1:10
    y = x;
  end
end

function loops_2
  for x = 1:10
    if x < 5
      a = x;
    end;
  end
end
