import pandas as pd
import json
import sys
import os

home = './'

def Extract(year, month, day):
	player_path = home + 'data/crawler/rotogrinders/projections/%s-%s-%s.json' % (year, month, day)
	player_json_data = json.loads(open(player_path, 'r').read())
	player_dict = {'name' : [], 'position' : [], 'slate_id' : [], 'slate_type' : [], 'player_id' : [], 'salary' : [], 'points' : []}
	showdown_player = {}
	idx = 0
	for data in player_json_data:
		if data['import_data'] is None:
			print 'None import_data for ' + data['player_name']
			continue
		for slate in data['import_data']:
			player_dict['points'].append(slate['fpts'])
			player_dict['slate_id'].append(slate['slate_id'])
			player_dict['slate_type'].append(slate['type'])
			player_dict['player_id'].append(slate['player_id'])
			player_dict['salary'].append(slate['salary'])
			# rotogrinders doesn't have CPT/UTIL position data for showdown captain mode
			if slate['type'] == 'showdown captain mode':
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
	player_df.to_csv(home + 'data/extractor/rotogrinders/projections/%s-%s-%s.csv' % (year, month, day))

	slate_path = home + 'data/crawler/rotogrinders/slates/%s-%s-%s.json' % (year, month, day)
	slate_json_data = json.loads(open(slate_path, 'r').read())
	slate_dict = {'date' : [], 'name' : [], 'id' : []}
	for key, value in slate_json_data.iteritems():
		slate_dict['date'].append(value['date'])
		slate_dict['name'].append(key);
		slate_dict['id'].append(value['importId'] if key != 'All Games' else '0')
	slate_df = pd.DataFrame.from_dict(slate_dict)
	slate_df.set_index('name', inplace=True)
	slate_df.to_csv(home + 'data/extractor/rotogrinders/slates/%s-%s-%s.csv' % (year, month, day))

def ExtractStats():
	crawler_game_log_path = home + 'data/crawler/nba_stats/player_game_log/2018-19'
	analysis_dic = {'name' : [], 'GP' : [], 'DK_AVG' : [], 'DK_STD' : []}
	for file_name in os.listdir(crawler_game_log_path):
		player_name = file_name.split('.')[0]
		game_log = pd.read_csv(crawler_game_log_path + '/' + file_name)
		if game_log.empty:
			continue
		analysis_dic['name'].append(player_name)
		analysis_dic['DK_AVG'].append(game_log['DKP'].mean())
		analysis_dic['DK_STD'].append(game_log['DKP'].std())
		analysis_dic['GP'].append(len(game_log.index))
	analysis_df = pd.DataFrame.from_dict(analysis_dic)
	analysis_df['DK_COV'] = analysis_df['DK_STD'] / analysis_df['DK_AVG']
	analysis_df.set_index('name', inplace=True)
	analysis_df.to_csv(home + 'data/extractor/stats/player_analysis.csv')

if __name__ == "__main__":
	year = sys.argv[1]
	month = sys.argv[2]
	day = sys.argv[3]
	Extract(year, month, day)
	ExtractStats()