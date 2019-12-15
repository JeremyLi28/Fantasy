import pandas as pd
import sys
from operator import itemgetter
import heapq
import os
from optparse import OptionParser
import datetime
from pydfs_lineup_optimizer import get_optimizer, Site, Sport, Player

def IPOptimizer(source, date, top_k, slate_id):
	projections_path = home + 'data/extractor/%s/projections/%s.csv' % (source, date)
	if not os.path.exists(projections_path):
		print "projections for %s not exists" % date
		return []
	projections_data = pd.read_csv(projections_path, header = 0, index_col = 0)
	projections_data.drop_duplicates('player_id', inplace=True)

	if slate_id not in projections_data['slate_id'].tolist():
		print "%d not exist!" % slate_id
		return []
	slate_type = projections_data[projections_data['slate_id'] == slate_id]['slate_type'][0]
	if slate_type != 'classic':
		print "%s not supported!" % slate_type
		return []

	players = []
	for i, p in projections_data[projections_data['slate_id'] == slate_id].iterrows():
		players.append(Player(p['player_id'], i.split(' ')[0], i.split(' ')[1], p['position'].split('/'), 'Team', p['salary'], p['points']))
		optimizer = get_optimizer(Site.DRAFTKINGS, Sport.BASKETBALL)
	optimizer.load_players(players)
	lineups = optimizer.optimize(n=top_k)
	results = []
	for lineup in lineups:
		r = [p.full_name for p in lineup.lineup]
		r.append(lineup.fantasy_points_projection)
		r.append(lineup.salary_costs)
		results.append(r)
	return results

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--date", dest="date", default=datetime.datetime.today().strftime('%Y-%m-%d'))
	parser.add_option("-k", "--top_k", dest="top_k", default=2)
	parser.add_option("-s", "--slate", dest="slate_id")
	(options, args) = parser.parse_args()
	DPOptimizer('rotogrinders', options.date, options.top_k, int(options.slate_id))
