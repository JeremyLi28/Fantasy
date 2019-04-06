import pandas as pd
import numpy as np
import os
import sys
from optparse import OptionParser
import datetime

home = './'

# DK results data is parsed from rotoguru daily, in the format of
# http://rotoguru1.com/cgi-bin/hyday.pl?mon=11&day=10&year=2018&game=dk&scsv=1
# results will be stored in
def fetch_dk_result(date):
	crawler_game_log_path = home + 'data/crawler/nba_stats/player_game_log/2018-19'
	result_dic = {'name' : [], 'DKP': []}
	for file_name in os.listdir(crawler_game_log_path):
		player_name = file_name.split('.')[0]
		game_log = pd.read_csv(crawler_game_log_path + '/' + file_name)
		if game_log.empty:
			continue
		if not game_log[game_log['GAME_DATE'] == date].empty:
			result_dic['name'].append(player_name)
			result_dic['DKP'].append(game_log[game_log['GAME_DATE'] == date].iloc[0]['DKP'])

	result_df = pd.DataFrame.from_dict(result_dic)
	result_df.set_index('name', inplace=True)
	return result_df


def fetch_rg_proj(date):
	proj_path = home + 'data/extractor/rotogrinders/projections/%s.csv' % date
	proj_data = pd.read_csv(proj_path, header=0, index_col=0)
	return proj_data[proj_data['slate_type'] == 'classic'][['points', 'salary']].drop_duplicates()

def result_analysis(date):
	res = fetch_dk_result(date)
	rg_proj = fetch_rg_proj(date)
	join_res_rg = res.join(rg_proj, how='inner', on='name')[['DKP', 'salary', 'points']]
	join_res_rg.columns = ['DKP', 'DKS', 'RGP']
	rmse = pow(join_res_rg['DKP'] - join_res_rg['RGP'], 2)
	mae = abs(join_res_rg['DKP'] - join_res_rg['RGP'])
	print "RG RMSE: " + str(np.sqrt(rmse.sum() / len(join_res_rg)) / join_res_rg['DKP'].mean())
	print "RG MAE: " + str(mae.sum() / len(join_res_rg) / join_res_rg['DKP'].mean())
	print "Proj/Res: " + str(join_res_rg['RGP'].sum() / join_res_rg['DKP'].sum())

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--date", dest="date", default=datetime.datetime.today().strftime('%Y-%m-%d'))
	(options, args) = parser.parse_args()
	result_analysis(options.date)