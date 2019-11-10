import pandas as pd
import numpy as np
import os
import sys
from optparse import OptionParser
import datetime
from datetime import timedelta, date, datetime

home = './'

def daterange(start_date, end_date):
	start_date = datetime.strptime(start_date, '%Y-%m-%d')
	end_date = datetime.strptime(end_date, '%Y-%m-%d')
	for n in range(int ((end_date - start_date).days)):
		yield start_date + timedelta(n)

def DailyResultCollector(date):
	crawler_game_log_path = home + 'data/crawler/nba_stats/player_game_log/2018-19'
	result_dic = {'name' : [], 'MIN' : [], 'PTS' :[], 'AST' : [], 'REB' : [], 'STL' : [], 'BLK' : [], 'TOV' : [], 'DKP' : []}
	for file_name in os.listdir(crawler_game_log_path):
		player_name = os.path.splitext(file_name)[0]
		game_log = pd.read_csv(crawler_game_log_path + '/' + file_name)
		if game_log.empty:
			continue
		if not game_log[game_log['GAME_DATE'] == date].empty:
			result_dic['name'].append(player_name)
			result_dic['MIN'].append(game_log[game_log['GAME_DATE'] == date].iloc[0]['MIN'])
			result_dic['PTS'].append(game_log[game_log['GAME_DATE'] == date].iloc[0]['PTS'])
			result_dic['AST'].append(game_log[game_log['GAME_DATE'] == date].iloc[0]['AST'])
			result_dic['REB'].append(game_log[game_log['GAME_DATE'] == date].iloc[0]['REB'])
			result_dic['STL'].append(game_log[game_log['GAME_DATE'] == date].iloc[0]['STL'])
			result_dic['BLK'].append(game_log[game_log['GAME_DATE'] == date].iloc[0]['BLK'])
			result_dic['TOV'].append(game_log[game_log['GAME_DATE'] == date].iloc[0]['TOV'])
			result_dic['DKP'].append(game_log[game_log['GAME_DATE'] == date].iloc[0]['DKP'])

	result_df = pd.DataFrame.from_dict(result_dic)
	result_df.set_index('name', inplace=True)
	if result_df.empty:
		print "%s data is empty" % date
		return
	dk_path = home + 'data/extractor/rotogrinders/projections/%s.csv' % date
	if not os.path.isfile(dk_path):
		print "No DK info for %s" % date
		return
	dk_info = pd.read_csv(dk_path, header=0)
	dk_info = dk_info[dk_info['slate_type'] == 'classic'][['name', 'salary']].drop_duplicates()
	dk_info.columns = ['name', 'DKS']
	dk_info.set_index('name', inplace=True)
	dk_info['DKS'] = dk_info['DKS'].astype(int)

	joined_result_df = result_df.join(dk_info, how='left', on='name')[['DKS', 'DKP', 'MIN', 'PTS', 'AST', 'REB', 'STL', 'BLK', 'TOV']]

	result_dir = home + 'data/results/daily'
	if not os.path.exists(result_dir):
		os.makedirs(result_dir)
	result_path = result_dir + '/%s.csv' % date
	joined_result_df.to_csv(result_path)
	print "Collect daily result for %s" % date


if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--date", dest="date", default=datetime.today().strftime('%Y-%m-%d'))
	parser.add_option("-s", "--start_date", dest="start_date", default="")
	parser.add_option("-e", "--end_date", dest="end_date", default="")
	(options, args) = parser.parse_args()
	if options.start_date == "" or options.end_date == "":
		options.start_date = options.date
		options.end_date = (datetime.strptime(options.date, '%Y-%m-%d') + timedelta(1)).strftime('%Y-%m-%d')
	for date in daterange(options.start_date, options.end_date):
		DailyResultCollector(date.strftime('%Y-%m-%d'))