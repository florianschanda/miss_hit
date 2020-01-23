% From https://www.mathworks.com/help/parallel-computing/distribute-arrays-and-run-spmd.html

function test_01()
  spmd
    INP = load(['somedatafile' num2str(labindex) '.mat']);
    RES = somefun(INP);
  end
end
