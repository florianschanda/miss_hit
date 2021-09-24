classdef MyTest < matlab.unittest.TestCase

    methods (Test, TestTags=['potato']) % nok
        function wibble1(self)
            self.verifyEqual(1, 1);
        end
    end

    methods (Test, TestTags={"potato"}) % nok
        function wibble2(self)
            self.verifyEqual(1, 1);
        end
    end

    methods (Test, TestTags=["potato"]) % ok
        function wibble3(self)
            self.verifyEqual(1, 1);
        end
    end

    methods (Test, TestTags={'potato'}) % ok
        function wibble4(self)
            self.verifyEqual(1, 1);
        end
    end

    methods (Test, TestTags='potato') % nok
        function wibble5(self)
            self.verifyEqual(1, 1);
        end
    end

    methods (Test, TestTags={'potato'; 'kitten'}) % nok
        function wibble6(self)
            self.verifyEqual(1, 1);
        end
    end

end
