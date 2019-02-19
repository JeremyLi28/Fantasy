import pandas as pd
import json
import sys

home = './'

def load_roto_grinders_proj(year, month, day):
	path = home + 'data/raw/rotogrinders/projections/%s-%s-%s.json' % (year, month, day)
	json_data = json.loads(open(path, 'r').read())
	rg_dict = {'name' : [], 'position' : [], 'salary' : [], 'points' : []}
	for data in json_data:
		rg_dict['name'].append(data['player_name'])
		rg_dict['position'].append(data['position'])
		rg_dict['salary'].append(data['salary'])
		rg_dict['points'].append(data['points'])
	rg_df = pd.DataFrame.from_dict(rg_dict)
	rg_df.set_index('name', inplace=True)
	rg_df.to_csv(home + 'data/extractor/rotogrinders_proj/%s-%s-%s.csv' % (year, month, day))


if __name__ == "__main__":
	year = sys.argv[1]
	month = sys.argv[2]
	day = sys.argv[3]
	load_roto_grinders_proj(year, month, day)