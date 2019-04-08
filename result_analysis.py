import pandas as pd
import numpy as np
import os
import sys
from optparse import OptionParser
import datetime
from datetime import timedelta, date, datetime

home = './'

def daterange(start_date, end_date):
	for n in range(int ((end_date - start_date).days)):
		yield start_date + timedelta(n)

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
	if not os.path.isfile(proj_path):
		return pd.DataFrame()
	proj_data = pd.read_csv(proj_path, header=0, index_col=0)
	return proj_data[proj_data['slate_type'] == 'classic'][['points', 'salary']].drop_duplicates()

def result_analysis(date, report):
	res = fetch_dk_result(date)
	rg_proj = fetch_rg_proj(date)
	if res.empty or rg_proj.empty:
		print date + " data missing"
		return -1, -1, -1
	join_res_rg = res.join(rg_proj, how='inner', on='name')[['DKP', 'salary', 'points']]
	join_res_rg.columns = ['DKP', 'DKS', 'RGP']
	rmse_df = pow(join_res_rg['DKP'] - join_res_rg['RGP'], 2)
	mae_df = abs(join_res_rg['DKP'] - join_res_rg['RGP'])
	rmse = np.sqrt(rmse_df.sum() / len(join_res_rg)) / join_res_rg['DKP'].mean()
	mae = mae_df.sum() / len(join_res_rg) / join_res_rg['DKP'].mean()
	tp = join_res_rg['RGP'].sum() / join_res_rg['DKP'].sum()
	if report:
		print date + " RG RMSE: " + str(rmse) + ", " + "RG MAE: " + str(mae) + ", " + "Proj/Res: " + str(tp)
	return rmse, mae, tp

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--date", dest="date", default=datetime.today().strftime('%Y-%m-%d'))
	parser.add_option("-s", "--start_date", dest="start_date", default="")
	parser.add_option("-e", "--end_date", dest="end_date", default="")
	parser.add_option("-r", "--report", action="store_true", dest="report", default=False)
	(options, args) = parser.parse_args()
	if options.start_date == "" or options.end_date == "":
		result_analysis(options.date, options.report)
	else:
		result_dic = {'Date' : [], 'RMSE' : [], 'MAE': [], 'TP': []}
		for date in daterange(datetime.strptime(options.start_date, '%Y-%m-%d'), datetime.strptime(options.end_date, '%Y-%m-%d')):
			rmse, mae, tp = result_analysis(date.strftime('%Y-%m-%d'), options.report)
			if rmse != -1:
				result_dic['Date'].append(date.strftime('%Y-%m-%d'))
				result_dic['RMSE'].append(rmse)
				result_dic['MAE'].append(mae)
				result_dic['TP'].append(tp)
		result_df = pd.DataFrame.from_dict(result_dic)
		result_df.set_index('Date', inplace=True)
		result_path = home + 'data/results/projection_result.csv'
		if os.path.isfile(result_path):
			old_result_df = pd.DataFrame.from_csv(result_path, header=0, index_col=0)
			result_df = pd.concat(result_df, old_result_df).drop_duplicates()
		result_df.to_csv(result_path)