% (c) Copyright 2019 Florian Schanda

function invalid_08()
  cd ../...
  bar
  % considered to be cd '../' 'bar'
end
