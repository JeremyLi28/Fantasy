import pandas as pd
import sys
from operator import itemgetter
import heapq
import os
from optparse import OptionParser
import datetime
import draftfast
from utils import *

def Optimize(date, top_k, slate_id, projection_source):
	projections_path = GetMetaDataPath() + '/rotogrinders/projections/%s.csv' % (date)
	if not os.path.exists(projections_path):
		print("projections for %s not exists" % date)
		return
	projections = pd.read_csv(projections_path, header = 0, index_col = 0)

	slates_path = GetMetaDataPath() + '/draftkings/slates/%s.csv' % (date)
	if not os.path.exists(slates_path):
		print("slates for %s not exists" % date)
		return
	slates = pd.read_csv(slates_path, header = 0, index_col = 0)

	if slate_id not in slates['SLATE_ID'].tolist():
		print "slate %d not exist!" % slate_id
		return
	if slates[slates['SLATE_ID'] == slate_id]['SLATE_TYPE'].values[0] != 'CLASSIC':
		print("slate type %s not supported!" % slate_type)
		return

	players_path = GetMetaDataPath() + '/draftkings/players/%s.csv' % (date)
	players = pd.read_csv(players_path, header = 0, index_col = 0)
	players = players[players['SLATE_ID'] == slate_id]
	players.set_index('NAME', inplace=True)

	players_with_projection = players.join(projections)

	player_pool = []
	for name, data in players_with_projection.iterrows()::
		player_pool.append(Player(name = name, cost = data['SALARY'], proj = data['points']))

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--date", dest="date", default=datetime.datetime.today().strftime('%Y-%m-%d'))
	parser.add_option("-k", "--top_k", dest="top_k", default=2)
	parser.add_option("-s", "--slate", dest="slate_id")
	(options, args) = parser.parse_args()
	Optimize('rotogrinders', options.date, options.top_k, int(options.slate_id))
