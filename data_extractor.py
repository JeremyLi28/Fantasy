import pandas as pd
import json
import sys

home = './'

def Extract(year, month, day):
	player_path = home + 'data/crawler/rotogrinders/projections/%s-%s-%s.json' % (year, month, day)
	player_json_data = json.loads(open(player_path, 'r').read())
	player_dict = {'name' : [], 'position' : [], 'slate_id' : [], 'player_id': [], 'salary' : [], 'points' : []}
	for data in player_json_data:
		if data['import_data'] is None:
			print 'None import_data for ' + data['player_name']
			continue
		for slate in data['import_data']:
			player_dict['name'].append(data['player_name'])
			player_dict['position'].append(data['position'])
			player_dict['points'].append(data['points'])
			player_dict['slate_id'].append(slate['slate_id'])
			player_dict['player_id'].append(slate['player_id'])
			player_dict['salary'].append(slate['salary'])
	player_df = pd.DataFrame.from_dict(player_dict)
	player_df.set_index('name', inplace=True)
	player_df.to_csv(home + 'data/extractor/rotogrinders/projections/%s-%s-%s.csv' % (year, month, day))

	slate_path = home + 'data/crawler/rotogrinders/slates/%s-%s-%s.json' % (year, month, day)
	slate_json_data = json.loads(open(slate_path, 'r').read())
	slate_dict = {'name' : [], 'id' : []}
	for key, value in slate_json_data.iteritems():
		slate_dict['name'].append(key);
		slate_dict['id'].append(value['importId'] if key != 'All Games' else '0')
	slate_df = pd.DataFrame.from_dict(slate_dict)
	slate_df.set_index('name', inplace=True)
	slate_df.to_csv(home + 'data/extractor/rotogrinders/slates/%s-%s-%s.csv' % (year, month, day))

if __name__ == "__main__":
	year = sys.argv[1]
	month = sys.argv[2]
	day = sys.argv[3]
	Extract(year, month, day)