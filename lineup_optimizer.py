import pandas as pd
import sys
from operator import itemgetter
import heapq
import os

home = './'


def create_lineups(source, year, month, day, top_k, slate_name = "All Games"):
	projections_path = home + 'data/extractor/%s/projections/%s-%s-%s.csv' % (source, year, month, day)
	projections_data = pd.read_csv(projections_path, header = 0, index_col = 0)
	slates_path = home + 'data/extractor/rotogrinders/slates/%s-%s-%s.csv' % (year, month, day)
	slates_data = pd.read_csv(slates_path, header = 0, index_col = 0)

	if slate_name not in slates_data.index.tolist():
		print slate_name + " Not exist!"
		return
	slate_id = slates_data.loc[slate_name]['id']

	sgs = projections_data[projections_data['position'].str.contains('SG') & (projections_data['slate_id'] == slate_id)].index.tolist()
	pgs = projections_data[projections_data['position'].str.contains('PG') & (projections_data['slate_id'] == slate_id)].index.tolist()
	gs = projections_data[(projections_data['position'].str.contains('SG') | projections_data['position'].str.contains('PG')) & (projections_data['slate_id'] == slate_id)].index.tolist()
	sfs = projections_data[projections_data['position'].str.contains('SF') & (projections_data['slate_id'] == slate_id)].index.tolist()
	pfs = projections_data[projections_data['position'].str.contains('PF') & (projections_data['slate_id'] == slate_id)].index.tolist()
	fs = projections_data[(projections_data['position'].str.contains('SF') | projections_data['position'].str.contains('F')) & (projections_data['slate_id'] == slate_id)].index.tolist()
	cs = projections_data[projections_data['position'].str.contains('C') & (projections_data['slate_id'] == slate_id)].index.tolist()
	utils = projections_data[projections_data['slate_id'] == slate_id].index.tolist()

	players_by_pos = [sgs, pgs, gs, sfs, pfs, fs, cs, utils]

	lineups = optimize(50000, players_by_pos, projections_data[projections_data['slate_id'] == slate_id], top_k)
	lineups_df = pd.DataFrame([['rg_proj_%s' % (i + 1)] + lineup for i, lineup in enumerate(lineups)], \
		columns=['Name', 'SG', 'PG', 'G', 'SF', 'PF', 'F', 'C', 'UTIL', 'Points', 'Salary'])
	projections_dir = 'data/lineups/%s-%s-%s' % (year, month, day)
	if not os.path.exists(projections_dir):
		os.makedirs(projections_dir)
	lineups_df.to_csv(home + projections_dir + '/%s.csv' % (slate_name))

	gen_dk_result(lineups_df, projections_data[projections_data['slate_id'] == slate_id], slate_name)

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
            items.append(lineup)
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
                    if j + salary <= salary_cap / 100 and player not in set(l[1]) and len(l[1]) == i - 1:
                        lineup =  l[1][:]
                        lineup.append(player)
                        memory[i][j + salary].push(lineup, l[0] + data.loc[player]['points'])

    result = []
    while not memory[len(players_by_pos)][salary_cap / 100].empty():
        l = memory[len(players_by_pos)][salary_cap / 100].pop()
        points = lineup_points(l, data)
        salary = lineup_salary(l, data)
        l.append(points)
        l.append(salary * 100)
        result.insert(0, l)
    return result

def gen_dk_result(lineups_df, player_slate_id, slate_name):
    result = lineups_df[['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL']]
    result['PG'] = result['PG'].apply(lambda x : player_slate_id.loc[x, 'player_id'])
    result['SG'] = result['SG'].apply(lambda x : player_slate_id.loc[x, 'player_id'])
    result['SF'] = result['SF'].apply(lambda x : player_slate_id.loc[x, 'player_id'])
    result['PF'] = result['PF'].apply(lambda x : player_slate_id.loc[x, 'player_id'])
    result['C'] = result['C'].apply(lambda x : player_slate_id.loc[x, 'player_id'])
    result['G'] = result['G'].apply(lambda x : player_slate_id.loc[x, 'player_id'])
    result['F'] = result['F'].apply(lambda x : player_slate_id.loc[x, 'player_id'])
    result['UTIL'] = result['UTIL'].apply(lambda x : player_slate_id.loc[x, 'player_id'])
    result_dir = 'data/submissions/dk/%s-%s-%s' % (year, month, day)
    if not os.path.exists(result_dir):
		os.makedirs(result_dir)
    result.to_csv(home + result_dir + '/%s.csv' % (slate_name), index=False)

if __name__ == "__main__":
	year = sys.argv[1]
	month = sys.argv[2]
	day = sys.argv[3]
	top_k = int(sys.argv[4])
	slate_name = sys.argv[5]
	create_lineups('rotogrinders', year, month, day, top_k, slate_name)
