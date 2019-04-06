import pandas as pd
import sys
from operator import itemgetter
import heapq
import os
from optparse import OptionParser
import datetime

home = './'

def get_player_by_pos(projections_data, slates_data, slate_type, slate_id):
	if slate_type == 'classic':
		sgs = projections_data[projections_data['position'].str.contains('SG') & (projections_data['slate_id'] == slate_id)].index.tolist()
		pgs = projections_data[projections_data['position'].str.contains('PG') & (projections_data['slate_id'] == slate_id)].index.tolist()
		gs = projections_data[(projections_data['position'].str.contains('SG') | projections_data['position'].str.contains('PG')) & (projections_data['slate_id'] == slate_id)].index.tolist()
		sfs = projections_data[projections_data['position'].str.contains('SF') & (projections_data['slate_id'] == slate_id)].index.tolist()
		pfs = projections_data[projections_data['position'].str.contains('PF') & (projections_data['slate_id'] == slate_id)].index.tolist()
		fs = projections_data[(projections_data['position'].str.contains('SF') | projections_data['position'].str.contains('F')) & (projections_data['slate_id'] == slate_id)].index.tolist()
		cs = projections_data[projections_data['position'].str.contains('C') & (projections_data['slate_id'] == slate_id)].index.tolist()
		utils = projections_data[projections_data['slate_id'] == slate_id].index.tolist()
		return [sgs, pgs, gs, sfs, pfs, fs, cs, utils]
	elif slate_type == 'tiers':
		t1 = projections_data[projections_data['position'].str.contains('T1') & (projections_data['slate_id'] == slate_id)].index.tolist()
		t2 = projections_data[projections_data['position'].str.contains('T2') & (projections_data['slate_id'] == slate_id)].index.tolist()
		t3 = projections_data[projections_data['position'].str.contains('T3') & (projections_data['slate_id'] == slate_id)].index.tolist()
		t4 = projections_data[projections_data['position'].str.contains('T4') & (projections_data['slate_id'] == slate_id)].index.tolist()
		t5 = projections_data[projections_data['position'].str.contains('T5') & (projections_data['slate_id'] == slate_id)].index.tolist()
		t6 = projections_data[projections_data['position'].str.contains('T6') & (projections_data['slate_id'] == slate_id)].index.tolist()
		return [t1, t2, t3, t4, t5, t6]
	elif slate_type == 'showdown captain mode':
		cpt = projections_data[projections_data['position'].str.contains('CPT') & (projections_data['slate_id'] == slate_id)].index.tolist()
		utils = projections_data[projections_data['position'].str.contains('UTIL') & (projections_data['slate_id'] == slate_id)].index.tolist()
		return [cpt, utils, utils, utils, utils, utils]
	else:
		print slate_type + " not supported yet!"
		return []

def create_lineups(source, date, top_k, slate_name = "All Games"):
	projections_path = home + 'data/extractor/%s/projections/%s.csv' % (source, date)
	projections_data = pd.read_csv(projections_path, header = 0, index_col = 0)
	slates_path = home + 'data/extractor/rotogrinders/slates/%s.csv' % date
	slates_data = pd.read_csv(slates_path, header = 0, index_col = 0)

	if slate_name not in slates_data.index.tolist():
		print slate_name + " Not exist!"
		return
	slate_id = slates_data.loc[slate_name]['id']
	slate_type = slate_name.split(':')[2].strip().split('(')[0].lower().strip()

	players_by_pos = get_player_by_pos(projections_data, slates_data, slate_type, slate_id)

	lineups = optimize(50000, players_by_pos, projections_data[projections_data['slate_id'] == slate_id], top_k)

	store_lineups(lineups, projections_data[projections_data['slate_id'] == slate_id], slate_name, slate_type, slate_id)

def lineup_salary(lineup, data):
	salary = 0
	for player in lineup:
		salary += player_salary(player, data)
	return salary

def lineup_points(lineup, data):
	points = 0
	for player in lineup:
		points += player_points(player, data)
	return points

def player_salary(player, data):
	return data.loc[player]['salary']

def player_points(player, data):
	return data.loc[player]['points']

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
        print "Position: " + str(i) + "/" + str(len(players_by_pos))
        for j in range(salary_cap / 100 + 1):
            for l in memory[i - 1][j].items():
                for player in players_by_pos[i - 1]:
                	salary = player_salary(player, data)
                	salary = int(salary / 100)
                	points = player_points(player, data)
                	if j + salary <= salary_cap / 100 and player not in set(l[1]) and len(l[1]) == i - 1:
                		lineup =  l[1][:]
                		lineup.append(player.split('_')[0])
                		memory[i][j + salary].push(lineup, l[0] + points)

    result = []
    while not memory[len(players_by_pos)][salary_cap / 100].empty():
        l = memory[len(players_by_pos)][salary_cap / 100].pop()
        points = lineup_points(l, data)
        salary = lineup_salary(l, data)
        l.append(points)
        l.append(salary * 100)
        result.insert(0, l)
    return result

def store_lineups(lineups, projections_data, slate_name, slate_type, slate_id):
	projections_dir = 'data/lineups/%s' % date
	if not os.path.exists(projections_dir):
		os.makedirs(projections_dir)
	result_dir = 'data/submissions/dk/%s' % date
	if not os.path.exists(result_dir):
		os.makedirs(result_dir)
	if slate_type == 'classic':
		lineups_df = pd.DataFrame([['rg_%s' % (i + 1)] + lineup for i, lineup in enumerate(lineups)], \
			columns=['Name', 'SG', 'PG', 'G', 'SF', 'PF', 'F', 'C', 'UTIL', 'Points', 'Salary'])
		lineups_df.to_csv(home + projections_dir + '/%s.csv' % (slate_name))

		result = lineups_df[['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL']]
		result['PG'] = result['PG'].apply(lambda x : projections_data.loc[x, 'player_id'])
		result['SG'] = result['SG'].apply(lambda x : projections_data.loc[x, 'player_id'])
		result['SF'] = result['SF'].apply(lambda x : projections_data.loc[x, 'player_id'])
		result['PF'] = result['PF'].apply(lambda x : projections_data.loc[x, 'player_id'])
		result['C'] = result['C'].apply(lambda x : projections_data.loc[x, 'player_id'])
		result['G'] = result['G'].apply(lambda x : projections_data.loc[x, 'player_id'])
		result['F'] = result['F'].apply(lambda x : projections_data.loc[x, 'player_id'])
		result['UTIL'] = result['UTIL'].apply(lambda x : projections_data.loc[x, 'player_id'])
	elif slate_type == 'tiers':
		lineups_df = pd.DataFrame([['rg_%s' % (i + 1)] + lineup for i, lineup in enumerate(lineups)], \
			columns=['Name', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'Points', 'Salary'])
		lineups_df.to_csv(home + projections_dir + '/%s.csv' % (slate_name))

		result = lineups_df[['T1', 'T2', 'T3', 'T4', 'T5', 'T6']]
		result['T1'] = result['T1'].apply(lambda x : projections_data.loc[x, 'player_id'])
		result['T2'] = result['T2'].apply(lambda x : projections_data.loc[x, 'player_id'])
		result['T3'] = result['T3'].apply(lambda x : projections_data.loc[x, 'player_id'])
		result['T4'] = result['T4'].apply(lambda x : projections_data.loc[x, 'player_id'])
		result['T5'] = result['T5'].apply(lambda x : projections_data.loc[x, 'player_id'])
		result['T6'] = result['T6'].apply(lambda x : projections_data.loc[x, 'player_id'])
	elif slate_type == 'showdown captain mode':
		lineups_df = pd.DataFrame([['rg_%s' % (i + 1)] + lineup for i, lineup in enumerate(lineups)], \
			columns=['Name', 'CPT', 'UTIL1', 'UTIL2', 'UTIL3', 'UTIL4', 'UTIL5', 'Points', 'Salary'])
		lineups_df.to_csv(home + projections_dir + '/%s.csv' % (slate_name))

		result = lineups_df[['CPT', 'UTIL1', 'UTIL2', 'UTIL3', 'UTIL4', 'UTIL5']]
		result['CPT'] = result['CPT'].apply(lambda x : projections_data.loc[x, 'player_id'])
		result['UTIL1'] = result['UTIL1'].apply(lambda x : projections_data.loc[x, 'player_id'])
		result['UTIL2'] = result['UTIL2'].apply(lambda x : projections_data.loc[x, 'player_id'])
		result['UTIL3'] = result['UTIL3'].apply(lambda x : projections_data.loc[x, 'player_id'])
		result['UTIL4'] = result['UTIL4'].apply(lambda x : projections_data.loc[x, 'player_id'])
		result['UTIL5'] = result['UTIL5'].apply(lambda x : projections_data.loc[x, 'player_id'])
		result.columns = ['CPT', 'UTIL', 'UTIL', 'UTIL', 'UTIL', 'UTIL']
	else:
		print slate_type + " not supported yet!"
		return

	result.to_csv(home + result_dir + '/%s.csv' % (slate_name), index=False)


if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--date", dest="date", default=datetime.datetime.today().strftime('%Y-%m-%d'))
	parser.add_option("-k", "--top_k", dest="top_l", default=2)
	parser.add_option("-s", "--slate", dest="slate_name", default="All Games")
	create_lineups('rotogrinders', date, top_k, slate_name)
