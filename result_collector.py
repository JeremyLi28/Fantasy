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
		player_name = os.path.splitext(file_name)[0]
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

def collect_result(date):
	join_res_rg = pd.DataFrame();
	result_dir = home + 'data/results'
	if not os.path.exists(result_dir):
		os.makedirs(result_dir)
	result_path = result_dir + '/%s.csv' % date
	res = fetch_dk_result(date)
	rg = fetch_rg_proj(date)
	savg = pd.read_csv(home + 'data/projections/season_avg/%s.csv' % date, header=0, index_col=0)
	if res.empty or rg.empty or savg.empty:
		print date + " data missing"
		return
	join_res = res.join(rg, how='inner', on='name').join(savg, how='inner', on='name')[['DKP', 'salary', 'points', 'SAVG']]
	join_res.columns = ['DKP', 'DKS', 'RGP', 'SAVG']
	print "Collect result for %s" % date
	join_res.to_csv(result_path)


if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--date", dest="date", default=datetime.today().strftime('%Y-%m-%d'))
	parser.add_option("-s", "--start_date", dest="start_date", default="")
	parser.add_option("-e", "--end_date", dest="end_date", default="")
	(options, args) = parser.parse_args()
	if options.start_date == "" or options.end_date == "":
		collect_result(options.date)
	else:
		for date in daterange(datetime.strptime(options.start_date, '%Y-%m-%d'), datetime.strptime(options.end_date, '%Y-%m-%d')):
			collect_result(date.strftime('%Y-%m-%d'))