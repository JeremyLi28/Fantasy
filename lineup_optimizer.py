import pandas as pd
import sys
from operator import itemgetter
import heapq

home = './'

def create_lineups(source, year, month, day, top_k):
	path = home + 'data/extractor/%s/%s-%s-%s.csv' % (source, year, month, day)
	data = pd.read_csv(path, header = 0, index_col = 0)

	sgs = data[data['position'].str.contains('SG')].index.tolist()
	pgs = data[data['position'].str.contains('PG')].index.tolist()
	gs = data[data['position'].str.contains('SG') | data['position'].str.contains('PG')].index.tolist()
	sfs = data[data['position'].str.contains('SF')].index.tolist()
	pfs = data[data['position'].str.contains('PF')].index.tolist()
	fs = data[data['position'].str.contains('SF') | data['position'].str.contains('F')].index.tolist()
	cs = data[data['position'].str.contains('C')].index.tolist()
	utils = data.index.tolist()

	players_by_pos = [sgs, pgs, gs, sfs, pfs, fs, cs, utils]

	lineups = optimize(50000, players_by_pos, data, top_k)
	lineups_df = pd.DataFrame([['rg_proj_%s' % (i + 1)] + lineup for i, lineup in enumerate(lineups)], \
		columns=['Name', 'SG', 'PG', 'G', 'SF', 'PF', 'F', 'C', 'UTIL', 'Points', 'Salary'])
	lineups_df.to_csv(home + 'data/lineups/%s-%s-%s.csv' % (year, month, day))

def lineup_salary(lineup, data):
	salary = 0
	for player in lineup:
		salary += int(data.loc[player]['salary'] / 100)
	return salary

def lineup_points(lineup, data):
	points = 0
	for player in lineup:
		points += data.loc[player]['points']
	return points

def lineup_eq(lineup1, lineup2):
	return '_'.join(sorted(lineup1)) == '_'.join(sorted(lineup2))

class LineupPriorityQueue:
    def __init__(self, capacity):
        self.lineups = []
        self.lineups_set = set([])
        self.capacity = capacity
        
    def contains(self, lineup):
        return self.get_key(lineup) in self.lineups_set
    
    def push(self, lineup, priority):
        if self.contains(lineup):
            return
        heapq.heappush(self.lineups, [priority, lineup])
        self.lineups_set.add(self.get_key(lineup))
        if len(self.lineups) > self.capacity:
            self.pop()
            
    def pop(self):
        if len(self.lineups) == 0:
            return [] 
        min_lineup = heapq.heappop(self.lineups)
        self.lineups_set.remove(self.get_key(min_lineup[1]))
        return min_lineup[1]
    
    def get_key(self, lineup):
        return '|'.join(sorted(lineup))
    
    def items(self):
        items = []
        for lineup in self.lineups:
            items.append(lineup[1])
        return items
    
    def empty(self):
        return len(self.lineups) == 0

def optimize(salary_cap, players_by_pos, data, top_k):
    memory = [[LineupPriorityQueue(top_k) for j in range(salary_cap / 100 + 1)] for i in range(len(players_by_pos) + 1)]
    for j in range(salary_cap / 100 + 1):
        memory[0][j].push([], lineup_points([], data))
    for i in range(1, len(players_by_pos) + 1):
        print "Position: ", i
        for j in range(salary_cap / 100 + 1):
            for l in memory[i - 1][j].items():
                for player in players_by_pos[i - 1]:
                    salary = int(data.loc[player]['salary'] / 100)
                    if j + salary <= salary_cap / 100 and player not in set(l) and len(l) == i - 1:
                        lineup =  l[:]
                        lineup.append(player)
                        memory[i][j + salary].push(lineup, lineup_points(lineup, data))

    result = []
    while not memory[len(players_by_pos)][salary_cap / 100].empty():
        l = memory[len(players_by_pos)][salary_cap / 100].pop()
        points = lineup_points(l, data)
        salary = lineup_salary(l, data)
        l.append(points)
        l.append(salary * 100)
        result.insert(0, l)
    return result

if __name__ == "__main__":
	year = sys.argv[1]
	month = sys.argv[2]
	day = sys.argv[3]
	create_lineups('rotogrinders_proj', year, month, day, 10)
