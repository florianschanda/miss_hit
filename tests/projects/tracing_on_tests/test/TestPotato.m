classdef TestPotato < matlab.unittest.TestCase
    
    methods (Test, TestTags = {'Something'})
        function test_01 (self)
            self.verifyEqual(5, util.potato(4));
        end
    end
    
end

