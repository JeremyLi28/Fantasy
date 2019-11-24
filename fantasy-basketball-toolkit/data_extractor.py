import pandas as pd
import json
import sys
import os
from optparse import OptionParser
import datetime
from datetime import timedelta, date, datetime
from utils import *


def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

def RGExtractor(date):
	player_path = home + 'data/crawler/rotogrinders/projections/%s.json' % (date)
	if not os.path.isfile(player_path):
		print("crawler data for %s not exist!" % date)
		return
	player_json_data = json.loads(open(player_path, 'r').read())
	player_dict = {'name' : [], 'position' : [], 'slate_id' : [], 'slate_type' : [], 'player_id' : [], 'salary' : [], 'points' : []}
	showdown_player = {}
	idx = 0
	for data in player_json_data:
		if data['import_data'] is None:
			print('None import_data for ' + data['player_name'])
			continue
		for slate in data['import_data']:
			player_dict['points'].append(slate['fpts'])
			player_dict['slate_id'].append(slate['slate_id'])
			slate_type = slate['type'] if 'type' in slate else 'missing'
			player_dict['slate_type'].append(slate_type)
			player_dict['player_id'].append(slate['player_id'])
			player_dict['salary'].append(slate['salary'])
			# rotogrinders doesn't have CPT/UTIL position data for showdown captain mode
			if slate_type == 'showdown captain mode':
				if data['player_name'] not in showdown_player:
					showdown_player[data['player_name']] = idx
					player_dict['position'].append(slate['position'])
					player_dict['name'].append(data['player_name'])
				else:
					old_idx = showdown_player[data['player_name']]
					if int(player_dict['salary'][old_idx]) > int(slate['salary']):
						player_dict['position'][old_idx] = 'CPT'
						player_dict['position'].append('UTIL')
						player_dict['name'][old_idx] = player_dict['name'][old_idx] + '_cpt'
						player_dict['name'].append(data['player_name'])
					else:
						player_dict['position'][old_idx] = 'UTIL'
						player_dict['position'].append('CPT')
						player_dict['name'].append(data['player_name'] + '_cpt')
			else:
				player_dict['position'].append(slate['position'])
				player_dict['name'].append(data['player_name'])
			idx += 1	   
	player_df = pd.DataFrame.from_dict(player_dict)
	player_df.set_index('name', inplace=True)
	player_df.to_csv(home + 'data/extractor/rotogrinders/projections/%s.csv' % (date))

	slate_path = home + 'data/crawler/rotogrinders/slates/%s.json' % (date)
	slate_json_data = json.loads(open(slate_path, 'r').read())
	slate_dict = {'date' : [], 'name' : [], 'id' : []}
	for key, value in slate_json_data.iteritems():
		slate_dict['date'].append(value['date'])
		slate_dict['name'].append(key);
		slate_dict['id'].append(value['importId'] if key != 'All Games' else '0')
	slate_df = pd.DataFrame.from_dict(slate_dict)
	slate_df.set_index('name', inplace=True)
	slate_df.to_csv(home + 'data/extractor/rotogrinders/slates/%s.csv' % (date))
	print("Extract RotogGinders data for %s" % (date))
	print("========== Slate =========")
	print(slate_df)
	print("========= Projections %d ========" % len(player_df))
	print(player_df.head())
	print("....")

def GameLogExtractor(season, season_type):
	crawler_game_log_path = home + 'data/crawler/nba_stats/player_game_log/2018-19'
	analysis_dic = {'Name' : [], 'GP' : [], 'DKP' : [], 'DKP_STD' : [], 'DKP/M' : [], 'DKP/M_STD' : []}
	for file_name in os.listdir(crawler_game_log_path):
		player_name = file_name.split('.')[0]
		game_log = pd.read_csv(crawler_game_log_path + '/' + file_name)
		if game_log.empty:
			continue
		analysis_dic['Name'].append(player_name)
		analysis_dic['DKP'].append(game_log['DKP'].mean())
		analysis_dic['DKP_STD'].append(game_log['DKP'].std())
		analysis_dic['GP'].append(len(game_log.index))
		analysis_dic['DKP/M'].append((game_log['DKP'] / game_log['MIN']).mean())
		analysis_dic['DKP/M_STD'].append((game_log['DKP'] / game_log['MIN']).std())
	analysis_df = pd.DataFrame.from_dict(analysis_dic)
	analysis_df['DKP_COV'] = analysis_df['DKP_STD'] / analysis_df['DKP']
	analysis_df['DKP/M_COV'] = analysis_df['DKP/M_STD'] / analysis_df['DKP/M']
	analysis_df.set_index('Name', inplace=True)
	analysis_df[['GP', 'DKP', 'DKP_COV', 'DKP/M', 'DKP/M_COV']].to_csv(home + 'data/extractor/stats/player_analysis.csv')
	print("Extract NBA game log for %s %s" % (season, season_type))

def ResultExtractor(date):
	results_dir = home + 'data/extractor/results'
	if not os.path.exists(results_dir):
		os.makedirs(results_dir)
	if not os.path.exists(results_dir + '/slates'):
		os.makedirs(results_dir + '/slates')
	if not os.path.exists(results_dir + '/contests'):
		os.makedirs(results_dir + '/contests')
	slates_result_file = home + 'data/crawler/results/slates/%s.json' % date
	slates_dict = {'Id' : [], 'GPPAvg': [], 'CashAvg': []}
	slates = json.loads(open(slates_result_file, 'r').read())
	for slate in slates:
		slates_dict['Id'].append(slate['siteSlateId'])
		if 'summary' in slate:
			slates_dict['GPPAvg'].append(slate['summary']['gppAverage'])
			slates_dict['CashAvg'].append(slate['summary']['cashAverage'])
		else:
			slates_dict['GPPAvg'].append(0)
			slates_dict['CashAvg'].append(0)
	slates_df = pd.DataFrame.from_dict(slates_dict)
	slates_df.set_index('Id', inplace=True)
	slates_df.to_csv(results_dir + '/slates/%s.csv' % date)
	print("Extract results for %s" % date)

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--date", dest="date", default=datetime.today().strftime('%Y-%m-%d'))
	parser.add_option("-s", "--start_date", dest="start_date", default="")
	parser.add_option("-e", "--end_date", dest="end_date", default="")
	parser.add_option("-t", dest="crawler_type", default='RG')
	(options, args) = parser.parse_args()
	if options.crawler_type == 'RG':
		if options.start_date == "" or options.end_date == "":
			RGExtractor(options.date)
		else:
			for date in daterange(datetime.strptime(options.start_date, '%Y-%m-%d'), datetime.strptime(options.end_date, '%Y-%m-%d')):
				RGExtractor(date.strftime('%Y-%m-%d'))
	elif options.crawler_type == 'GameLog':
		GameLogExtractor('2018-19', 'Regular Season')
	elif options.crawler_type == 'Result':
		if options.start_date == "" or options.end_date == "":
			ResultExtractor(options.date)
		else:
			for date in daterange(datetime.strptime(options.start_date, '%Y-%m-%d'), datetime.strptime(options.end_date, '%Y-%m-%d')):
				ResultExtractor(date.strftime('%Y-%m-%d'))
	else:
		print("Extractor type %s not supported yet." % options.crawler_type)