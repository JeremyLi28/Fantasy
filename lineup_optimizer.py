import pandas as pd
import sys
from operator import itemgetter

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
	lineups_df = pd.DataFrame([['rg_proj_%s' % (i + 1)] + lineup[0] + lineup[1] for i, lineup in enumerate(lineups)], \
		columns=['Name', 'SG', 'PG', 'G', 'SF', 'PF', 'F', 'C', 'UTIL', 'Points', 'Salary'])
	lineups_df.to_csv(home + 'data/lineups/%s-%s-%s.csv' % (year, month, day))



def optimize(salary_cap, players_by_pos, data, top_k):
    memory = [[[[], 0] for j in range(salary_cap / 100 + 1)] for i in range(len(players_by_pos) + 1)]
    for i in range(1, len(players_by_pos) + 1):
        for j in range(salary_cap / 100 + 1):
            for player in players_by_pos[i - 1]:
                salary = int(data.loc[player]['salary'] / 100)
                points = data.loc[player]['points']
                if j + salary <= salary_cap / 100 and memory[i - 1][j][1] + points > memory[i][j + salary][1] \
                    and player not in set(memory[i - 1][j][0]) and len(memory[i - 1][j][0]) == i - 1:
                    memory[i][j + salary][0] = memory[i - 1][j][0][:]
                    memory[i][j + salary][0].append(player)
                    memory[i][j + salary][1] = memory[i - 1][j][1] + points
    for i in range(salary_cap / 100 + 1):
        memory[len(players_by_pos)][i][1] = [memory[len(players_by_pos)][i][1] , i * 100]
    return sorted(memory[len(players_by_pos)], key=itemgetter(1), reverse=True)[0 : top_k]

if __name__ == "__main__":
	year = sys.argv[1]
	month = sys.argv[2]
	day = sys.argv[3]
	create_lineups('rotogrinders_proj', year, month, day, 10)
