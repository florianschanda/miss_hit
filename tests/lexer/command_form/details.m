% (c) Copyright 2019 Florian Schanda

function test_06()
  wibble a b  % wibble('a', 'b')

  wibble a...
         b % ditto

  wibble a....
         b % ditto

  wible "a    b" % wibble ('"a', 'b"')

  wibble 'a b' c % wibble('a b', 'c')

  wibble a b %c % wibble('a', 'b')

  wibble a b% wibble('a', 'b')

  wibble 'a' ...
         ...
         b % c  % wibble('a', 'b')

  wibble ../.././a b % wibble('../.././a', 'b')
end
