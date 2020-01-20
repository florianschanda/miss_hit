% (c) Copyright 2019 Florian Schanda

function odd()
  % I am pretty sure this is a MATLAB bug
  wibble a' 'b c  % wibble('a b', 'c')
  wibble [a 1 b] c % wibble('[a 1 b]', 'c')
  wibble [a 1 b) c % wibble('[a 1 b)', 'c')
  wibble a 1) % wibble('a', '1) ')
  wibble [a 1 b c % wibble('[a 1 b c ')
end
