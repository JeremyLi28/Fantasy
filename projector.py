import pandas as pd
from optparse import OptionParser
import datetime
from datetime import timedelta, date, datetime
import time
import os

home = './'

def daterange(start_date, end_date):
	start_date = datetime.strptime(start_date, '%Y-%m-%d')
	end_date = datetime.strptime(end_date, '%Y-%m-%d')
	for n in range(int ((end_date - start_date).days)):
		yield start_date + timedelta(n)

def RotogrindersProjector(proj_type, date):
	rg_path = home + 'data/extractor/rotogrinders/projections/%s.csv' % date
	if not os.path.isfile(rg_path):
		print "No projections for %s" % date
		return
	proj_data = pd.read_csv(rg_path, header=0, index_col=0)
	proj = proj_data[proj_data['slate_type'] == 'classic'][['points', 'salary']].drop_duplicates()
	proj.columns = ['Proj', 'DKS']
	proj_path = home +'data/projections/%s' % proj_type
	if not os.path.exists(proj_path):
		os.makedirs(proj_path)
	proj[['Proj']].to_csv(proj_path + '/%s.csv' % date)
	print "Rotogrinders projection for %s" % date


def SeasonAvgProjector(proj_type, date):
	proj_path = home +'data/projections/%s' % proj_type
	if not os.path.exists(proj_path):
		os.makedirs(proj_path)
	crawler_game_log_path = home + 'data/crawler/nba_stats/player_game_log/2018-19'
	result_dic = {'name' : [], 'Proj': []}
	for file_name in os.listdir(crawler_game_log_path):
		player_name = os.path.splitext(file_name)[0]
		game_log = pd.read_csv(crawler_game_log_path + '/' + file_name)
		if game_log.empty:
			continue
		if not game_log[game_log['GAME_DATE'] < date].empty:
			result_dic['name'].append(player_name)
			result_dic['Proj'].append(game_log[game_log['GAME_DATE'] < date]['DKP'].mean())

	result_df = pd.DataFrame.from_dict(result_dic)
	result_df.set_index('name', inplace=True)
	if result_df.empty:
		print "No projections for %s" % date
		return
	result_df.to_csv(proj_path + '/%s.csv' % date)
	print "Season avg projection for %s" % date

def RollingAvgProjector(proj_type, date):
	n = int(proj_type.split('_')[-1])
	proj_path = home +'data/projections/%s' % proj_type
	if not os.path.exists(proj_path):
		os.makedirs(proj_path)
	crawler_game_log_path = home + 'data/crawler/nba_stats/player_game_log/2018-19'
	result_dic = {'name' : [], 'Proj': []}
	for file_name in os.listdir(crawler_game_log_path):
		player_name = os.path.splitext(file_name)[0]
		game_log = pd.read_csv(crawler_game_log_path + '/' + file_name)
		if game_log.empty:
			continue
		if not game_log[game_log['GAME_DATE'] < date].empty:
			result_dic['name'].append(player_name)
			result_dic['Proj'].append(game_log[game_log['GAME_DATE'] < date][-n:]['DKP'].mean())

	result_df = pd.DataFrame.from_dict(result_dic)
	result_df.set_index('name', inplace=True)
	if result_df.empty:
		print "No projections for %s" % date
		return
	result_df.to_csv(proj_path + '/%s.csv' % date)
	print "Rolling avg %s projection for %s" % (n, date)

if __name__ == "__main__":
	proj_path = home +'data/projections'
	if not os.path.exists(proj_path):
		os.makedirs(proj_path)
	parser = OptionParser()
	parser.add_option("-d", "--date", dest="date", default=datetime.today().strftime('%Y-%m-%d'))
	parser.add_option("-s", "--start_date", dest="start_date", default="")
	parser.add_option("-e", "--end_date", dest="end_date", default="")
	parser.add_option("-t", "--type",  dest="proj_type", default="season_avg")
	(options, args) = parser.parse_args()
	if options.start_date == "" or options.end_date == "":
		options.start_date = options.date
		options.end_date = (datetime.strptime(options.date, '%Y-%m-%d') + timedelta(1)).strftime('%Y-%m-%d')

	if options.proj_type == "season_avg":
		projector = SeasonAvgProjector
	elif options.proj_type.startswith("rolling_avg"):
		projector = RollingAvgProjector
	elif options.proj_type == 'rotogrinders':
		projector = RotogrindersProjector
	else:
		print "%s not supported!" % options.proj_type

	for date in daterange(options.start_date, options.end_date):
		projector(options.proj_type, date.strftime('%Y-%m-%d'))
