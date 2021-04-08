function test(x)
   arguments % keyword
      x uint
   end
   try
      arguments = 12; % identifier
   end
   arguments = 42; % keyword again not allowed in MISS_HIT
end
