'''
Created on Jun 21, 2012

@author: Anthony Honstain
'''

import unittest
import CalculateRaceRank as CRR


class Test_groupdRaces(unittest.TestCase):

    def setUp(self):
        self.simpleresults = [  
                   CRR.RaceResult('2011-01-01 14:26:42-08', 1, 'SB A Main', 1, 'racer1', 1),
                   CRR.RaceResult('2011-01-01 14:26:42-08', 1, 'SB A Main', 2, 'racer2', 2),
                   
                   CRR.RaceResult('2011-01-03 14:24:52-08', 1, 'SB A Main', 1, 'racer1', 1),
                   CRR.RaceResult('2011-01-03 14:24:52-08', 1, 'SB A Main', 2, 'racer2', 2),
                   ]

    def test_groupRaces(self):
        expected = [[
                   CRR.RaceResult('2011-01-01 14:26:42-08', 1, 'SB A Main', 1, 'racer1', 1),
                   CRR.RaceResult('2011-01-01 14:26:42-08', 1, 'SB A Main', 2, 'racer2', 2),
                   ],[
                   CRR.RaceResult('2011-01-03 14:24:52-08', 1, 'SB A Main', 1, 'racer1', 1),
                   CRR.RaceResult('2011-01-03 14:24:52-08', 1, 'SB A Main', 2, 'racer2', 2),
                   ]]
        
        self.assertListEqual(CRR._groupRaces(self.simpleresults), 
                             expected)        
        
class Test_groupRaces_Bmains(unittest.TestCase):

    def setUp(self):
        self.simpleresults = [  
                   CRR.RaceResult('2011-01-01 14:26:42-08', 1, 'SB B Main', 3, 'racer3', 1),
                   CRR.RaceResult('2011-01-01 14:26:42-08', 1, 'SB B Main', 4, 'racer4', 2),
                   
                   CRR.RaceResult('2011-01-03 14:24:52-08', 1, 'SB A Main', 1, 'racer1', 1),
                   CRR.RaceResult('2011-01-03 14:24:52-08', 1, 'SB A Main', 2, 'racer2', 2),
                   ]

    def test_groupRaces_Bmains(self):
        expected = [[
                   CRR.RaceResult('2011-01-03 14:24:52-08', 1, 'SB A Main', 1, 'racer1', 1),
                   CRR.RaceResult('2011-01-03 14:24:52-08', 1, 'SB A Main', 2, 'racer2', 2),
                   CRR.RaceResult('2011-01-01 14:26:42-08', 1, 'SB B Main', 3, 'racer3', 3),
                   CRR.RaceResult('2011-01-01 14:26:42-08', 1, 'SB B Main', 4, 'racer4', 4),
                   ]]
        
        self.assertListEqual(CRR._groupRaces(self.simpleresults), 
                             expected)


if __name__ == '__main__':  
    unittest.main()   
