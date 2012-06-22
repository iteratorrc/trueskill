'''
Created on Jun 20, 2012

@author: Anthony Honstain
'''

from __future__ import print_function
import trueskill

from optparse import OptionParser
import pgdb

import re


class RaceResult(object):
    def __init__(self, date, trackkey, racedata, racerid, name, finalpos):
        self.date = date
        self.trackkey = trackkey
        self.racedata = racedata
        self.racerid = racerid
        self.name = name
        self.finalpos = finalpos

    def __str__(self):
        return str(self.__dict__)
        
    def __eq__(self, other): 
        return self.__dict__ == other.__dict__
        

class Player(object):    
    def __init__(self):
        self.skill = (25.0, 25.0/3.0)
        self.racecount = 0
    
    def __str__(self):
        return "mu={0[0]:.3f}  sigma={0[1]:.3f} count={1}".format(self.skill, self.racecount)
    

def _fillDict(race, player_dict):
    '''
    Create all the racer objects with initial ranking, storing them
    in a dictionary for easy lookup.
    '''
    for racer in race:
        if (not player_dict.has_key(racer.name)):
            player_dict[racer.name] = Player()
            
            
def _setRankAndAdjust(race, player_dict):
    '''
    Use the race results to set the rank on each racer object and
    have trueskill adjust based on the results.
    '''
    players_to_adjust = []
    
    for racer in race:
        player_dict[racer.name].rank = racer.finalpos
        player_dict[racer.name].racecount += 1
        
        players_to_adjust.append(player_dict[racer.name])
    
    trueskill.AdjustPlayers(players_to_adjust)


def _findSkill(player_dict, grouped_races):
    '''
    Take all the race information, create new racer objects as needed, and 
    update skill estimates.
    '''
    displaycount = 0
    
    for race in grouped_races:
        displaycount+=1
        print(displaycount)

# I have left these commented out as they may be helpful in debugging.
#        print("\n" + "="*30)
#        print("Process New Race")
#        print("="*30)
            
        # Make sure each racer has a player object.
        _fillDict(race, player_dict)

#        for racer in race:
#            print(racer)
#            print('{0:20} {1}'.format(racer.name, player_dict[racer.name]))

        _setRankAndAdjust(race, player_dict)
    
#        print("-"*30, "\nUpdated Rank\n", "-"*30)
#        for racer in race:
#            print('{0:20} {1}'.format(racer.name, player_dict[racer.name]))


def _groupRaces(refined_results):
    '''
    Take a list of individual race results and group them into separate lists. 
    B,C,D, etc main events will be folded into a single event with the A-main.
        This is done because on that day of racing we consider everyone in the
        class is competing with each other.    
    '''
    # These are to keep track of what race we are processing.
    current_date = refined_results[0].date
    current_racedata = refined_results[0].racedata
    
    grouped_races = [[]]

    for result in refined_results:
        # I want to organize these into distinct races quickly.
        # Might be better to do this with a standalone query for each race?

        if ((current_date != result.date) or
            (current_racedata != result.racedata)):
            # Found new race
            current_date = result.date
            current_racedata = result.racedata
            
            grouped_races.append([])
            
        grouped_races[-1].append(result)

    # Warning - we need to throw out races of only 1 person. Nothing useful can
    # be calculated from it. I have waited till this stage on the off chance there 
    # is a sub-main with 1 person that will get folded into an a-main.

    # I need to group the A,B,C mains into a single race, since that day of competition
    # is a comparison of everyone.
    # Example - if you win the B-main, it looks the same as if you won the A,
    #     this is going to confuse things.
    pattern = re.compile("[B-Z][1-9]? main", re.IGNORECASE)
    
    grouped_mains = []    
    prev_race = grouped_races[0]
    
    for cur_race in grouped_races[1:]:
        # We are checking to see if the last race is a sub-main of this race.        
        start_index = pattern.search(prev_race[0].racedata)
        if (start_index != None):            
            # We found a sub A-main race.
            if (prev_race[0].trackkey != cur_race[0].trackkey):
                # Dirty data, we want to move on. It appears that there are sub-mains with 
                # no related A-mains.
                if (len(prev_race) > 1): # Ignore races of 1 person.
                    grouped_mains.append(prev_race)
                prev_race = cur_race
            else:            
                prev_race = _combineRace(prev_race, cur_race)
            
        else:
            if (len(prev_race) > 1): # Ignore races of 1 person.
                grouped_mains.append(prev_race)
            prev_race = cur_race    

    if (len(prev_race) > 1): # Ignore races of 1 person.
        grouped_mains.append(prev_race)    
       
    return grouped_mains


def _combineRace(prev_race, cur_race):
    last_place = cur_race[-1].finalpos
    
    if (prev_race[0].trackkey != cur_race[0].trackkey):
        raise Exception("Cannot merge races from different tracks.")
    for racer in prev_race:
        # IMPORTANT - Need to make sure bumped racers do not get calculated twice.
        if (racer not in cur_race):
            racer.finalpos += last_place
            cur_race.append(racer)

    return cur_race


def main():
    parser = OptionParser()

    parser.add_option("-d", "--database", dest="database",
                      help="database name")

    parser.add_option("-u", "--username", dest="username",
                      help="User name for database")

    parser.add_option("-p", "--password", dest="password",
                      help="Password for database")

    (options, args) = parser.parse_args()

    # ------------------------------------------------------------------
    # Connect to sql and get the results
    # ------------------------------------------------------------------
    sql = pgdb.connect(database=options.database, 
                       user=options.username,
                       password=options.password)
    
    _sql = sql 
    _racerName_tblname = "rcdata_racerid"
    _raceResult_tblname = "rcdata_singleraceresults"
    _laptimes_tblname = "rcdata_laptimes"
    
    # For each race I need race details, the name and position in the race.
    #     Starting SIMPLE - just considering finish position, not times.    
    
    cur = sql.cursor()
    get_racers_cmd = '''
        SELECT rdetails.racedate, rdetails.trackkey_id, rdetails.racedata, 
            racerid.id, racerid.racerpreferredname, rresult.finalpos  
        FROM ''' + _racerName_tblname + ''' as racerid , 
            '''+ _raceResult_tblname + ''' as rresult,
            rcdata_singleracedetails as rdetails 
        WHERE racerid.id = rresult.racerid_id AND 
            rresult.raceid_id = rdetails.id AND
            rdetails.racedata ilike '%main%' AND
            rdetails.racedata NOT ilike '%super%' AND
            rdetails.racedata ilike '%stock%' AND
            rdetails.racedata ilike '%buggy%'
        ORDER BY rdetails.racedate, rdetails.trackkey_id, rdetails.racedata, rresult.finalpos
        ;
        '''
    cur.execute(get_racers_cmd)
    results = cur.fetchall()
    cur.close()    

    # EXAMPLE of results, it is a big list of all the race info.
    #   [
    #    ['2011-01-24 14:53:16-08', 1, 'Modified Buggy A Main', 1, 'John Doe-1', 1],
    #    ['2011-01-24 14:53:16-08', 1, 'Modified Buggy A Main', 2, 'John Doe-2', 2],
    #    ['2011-01-24 14:53:16-08', 1, 'Modified Buggy A Main', 3, 'John Doe-3', 3],
    #    ['2011-01-24 14:53:16-08', 1, 'Modified Buggy A Main', 4, 'John Doe-4', 4],
    #    ['2011-01-26 15:29:45-08', 1, 'Modified Buggy A Main', 1, 'John Doe-1', 1],
    #    ['2011-01-26 15:29:45-08', 1, 'Modified Buggy A Main', 2, 'John Doe-2', 2],
    #    ...
     
    if (len(results) < 1):
        raise Exception("No results were returned from the database.")

    # ------------------------------------------------------------------
    # Convert the raw results from sql into a list of RaceResult objects.
    # ------------------------------------------------------------------
    refined_results = []
    for result in results:
        refined_results.append(RaceResult(result[0], 
                                          result[1], 
                                          result[2],
                                          result[3],
                                          result[4],
                                          result[5]))
    
    
    grouped_races = _groupRaces(refined_results)        

    # player_dict is a dictionary of 'players', they will be populated as races are processed.
    player_dict = {}
    
    # ------------------------------------------------------------------
    # Process all the results and run the skill estimation
    # ------------------------------------------------------------------
    _findSkill(player_dict, grouped_races)
        
        
    # ------------------------------------------------------------------
    # Prepare the results for display.
    # ------------------------------------------------------------------
    
    # Turn it into a list of tuples, then sort it
    trueskill_results = player_dict.items()
    
    # We only want to consider racers that have raced 10 times or more
    trueskill_results_filtered = filter(lambda x: x[1].racecount > 10, trueskill_results)
            
    # Calculate ranking
    display_rank = []
    for racer_tup in trueskill_results_filtered:
        display_rank.append((racer_tup[0], racer_tup[1].skill[0] - 3 * racer_tup[1].skill[1]))
    
    display_rank.sort(key=lambda tup: tup[1], reverse = True)
        
    print("*"*30 + "\nSummary\n" + "*"*30)
    print("Total Races:", len(grouped_races))
    print("Sanity - total number of race rows at start of processing:", len(results))
    count = 0
    for race in grouped_races:
        count += len(race)
    print("After processing:", count)

    print("*"*30 + "\nRanking\n" + "*"*30)
    for racer in display_rank:
        print('{0:20} Rank:{1:.2f}'.format(racer[0], racer[1]))


if __name__ == "__main__":
    main()