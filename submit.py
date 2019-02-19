import pandas as pd
import sys

home = './'

def submit_lineup(year, month, day):
	lineups_df = pd.read_csv(home + 'data/lineups/%s-%s-%s.csv' % (year, month, day), header = 0, index_col = 0)
	dk_id = pd.read_csv(home + 'data/other/dk_player_id/%s-%s-%s.csv' % (year, month, day), header = 0)[['Name', 'ID']]
	dk_id.columns = ['name', 'id']
	dk_id = dk_id.set_index('name')

	result = lineups_df[['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL']]
	result['PG'] = result['PG'].apply(lambda x : dk_id.loc[x, 'id'])
	result['SG'] = result['SG'].apply(lambda x : dk_id.loc[x, 'id'])
	result['SF'] = result['SF'].apply(lambda x : dk_id.loc[x, 'id'])
	result['PF'] = result['PF'].apply(lambda x : dk_id.loc[x, 'id'])
	result['C'] = result['C'].apply(lambda x : dk_id.loc[x, 'id'])
	result['G'] = result['G'].apply(lambda x : dk_id.loc[x, 'id'])
	result['F'] = result['F'].apply(lambda x : dk_id.loc[x, 'id'])
	result['UTIL'] = result['UTIL'].apply(lambda x : dk_id.loc[x, 'id'])
	result.to_csv(home + 'data/submissions/dk/%s-%s-%s.csv' % (year, month, day), index=False)

if __name__ == "__main__":
	year = sys.argv[1]
	month = sys.argv[2]
	day = sys.argv[3]
	submit_lineup(year, month, day)