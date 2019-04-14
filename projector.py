import pandas as pd
from optparse import OptionParser
import datetime
from datetime import timedelta, date, datetime
import time
import os

home = './'

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

def fetch_rg_proj(date):
	proj_path = home + 'data/extractor/rotogrinders/projections/%s.csv' % date
	if not os.path.isfile(proj_path):
		return pd.DataFrame()
	proj_data = pd.read_csv(proj_path, header=0, index_col=0)
	return proj_data[proj_data['slate_type'] == 'classic'][['points', 'salary']].drop_duplicates()

def season_avg(date):
	proj_path = home +'data/projections/season_avg'
	if not os.path.exists(proj_path):
		os.makedirs(proj_path)
	crawler_game_log_path = home + 'data/crawler/nba_stats/player_game_log/2018-19'
	result_dic = {'name' : [], 'SAVG': []}
	for file_name in os.listdir(crawler_game_log_path):
		player_name = os.path.splitext(file_name)[0]
		game_log = pd.read_csv(crawler_game_log_path + '/' + file_name)
		if game_log.empty:
			continue
		if not game_log[game_log['GAME_DATE'] < date].empty:
			result_dic['name'].append(player_name)
			result_dic['SAVG'].append(game_log[game_log['GAME_DATE'] < date]['DKP'].mean())

	result_df = pd.DataFrame.from_dict(result_dic)
	result_df.set_index('name', inplace=True)
	rg_proj = fetch_rg_proj(date)
	if rg_proj.empty:
		print "%s data missing" % date
		return
	joined_result_df = result_df.join(rg_proj, how='right', on='name')[['SAVG', 'points']]
	joined_result_df['SAVG'] = joined_result_df['SAVG'].fillna(joined_result_df['points'])
	joined_result_df[['SAVG']].to_csv(proj_path + '/%s.csv' % date)
	print "Season avg projection for %s" % date

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--date", dest="date", default=datetime.today().strftime('%Y-%m-%d'))
	parser.add_option("-s", "--start_date", dest="start_date", default="")
	parser.add_option("-e", "--end_date", dest="end_date", default="")
	parser.add_option("-t", "--type",  dest="proj_type", default="season_avg")
	(options, args) = parser.parse_args()
	if options.start_date == "" or options.end_date == "":
		if options.proj_type == "season_avg":
			season_avg(options.date)
	else:
		if options.proj_type == "season_avg":
			for date in daterange(datetime.strptime(options.start_date, '%Y-%m-%d'), datetime.strptime(options.end_date, '%Y-%m-%d')):
				season_avg(date.strftime('%Y-%m-%d'))