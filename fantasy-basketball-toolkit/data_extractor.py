import pandas as pd
import json
import sys
import os
from optparse import OptionParser
import datetime
from datetime import timedelta, date, datetime
from utils import *
import pytz


def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

def RGExtractor(date):
	rg_dir = GetMetaDataPath() + '/rotogrinders'
	projection_path = rg_dir + '/projections/raw/%s.json' % (date)
	if not os.path.isfile(projection_path):
		print("RG crawler data for %s not exist!" % date)
		return
	projection_json_data = json.loads(open(projection_path, 'r').read())
	projection_dict = {'NAME' : [], 'PROJECTION' : []}
	for data in projection_json_data:
		if data['import_data'] is None:
			print('None import_data for ' + data['player_name'])
			continue
		for slate in data['import_data']:
			projection_dict['NAME'].append(data['player_name'])
			projection_dict['PROJECTION'].append(slate['fpts'])
			break
	   
	projection_df = pd.DataFrame.from_dict(projection_dict)
	projection_df.set_index('NAME', inplace=True)
	projection_df.to_csv(rg_dir + '/projections/%s.csv' % (date))

	slate_path = rg_dir + '/slates/raw/%s.json' % (date)
	slate_json_data = json.loads(open(slate_path, 'r').read())
	slate_dict = {'DATE' : [], 'NAME' : [], 'ID' : []}
	for key, value in slate_json_data.items():
		slate_dict['DATE'].append(value['date'])
		slate_dict['NAME'].append(key)
		slate_dict['ID'].append(value['importId'] if key != 'All Games' else '0')
	slate_df = pd.DataFrame.from_dict(slate_dict)
	slate_df.set_index('NAME', inplace=True)
	slate_df.to_csv(rg_dir + '/slates/%s.csv' % (date))
	print("Extract RotogGinders data for %s" % (date))
	print("========== Slate =========")
	print(slate_df)
	print("========= Projections %d ========" % len(projection_df))
	print(projection_df.head())
	print("....")

def GameLogExtractor(season, season_type):
	crawler_game_log_path = home + 'data/crawler/nba_stats/player_game_log/2018-19'
	analysis_dic = {'Name' : [], 'GP' : [], 'DKP' : [], 'DKP_STD' : [], 'DKP/M' : [], 'DKP/M_STD' : []}
	for file_name in os.listdir(crawler_game_log_path):
		player_name = file_name.split('.')[0]
		game_log = pd.read_csv(crawler_game_log_path + '/' + file_name)
		if game_log.empty:
			continue
		analysis_dic['Name'].append(player_name)
		analysis_dic['DKP'].append(game_log['DKP'].mean())
		analysis_dic['DKP_STD'].append(game_log['DKP'].std())
		analysis_dic['GP'].append(len(game_log.index))
		analysis_dic['DKP/M'].append((game_log['DKP'] / game_log['MIN']).mean())
		analysis_dic['DKP/M_STD'].append((game_log['DKP'] / game_log['MIN']).std())
	analysis_df = pd.DataFrame.from_dict(analysis_dic)
	analysis_df['DKP_COV'] = analysis_df['DKP_STD'] / analysis_df['DKP']
	analysis_df['DKP/M_COV'] = analysis_df['DKP/M_STD'] / analysis_df['DKP/M']
	analysis_df.set_index('Name', inplace=True)
	analysis_df[['GP', 'DKP', 'DKP_COV', 'DKP/M', 'DKP/M_COV']].to_csv(home + 'data/extractor/stats/player_analysis.csv')
	print("Extract NBA game log for %s %s" % (season, season_type))

def MoneyLineExtractor(date):
	ml_dir = GetMetaDataPath() + '/draftkings/moneyline'
	CreateDirectoryIfNotExist(ml_dir + '/contests')
	CreateDirectoryIfNotExist(ml_dir + '/slates')

	slates_raw_file = ml_dir + '/slates/raw/%s.json' % date
	slates_dict = {'Id' : [], 'GPPAvg': [], 'CashAvg': []}
	slates = json.loads(open(slates_raw_file, 'r').read())
	for slate in slates:
		slates_dict['Id'].append(slate['siteSlateId'])
		if 'summary' in slate:
			slates_dict['GPPAvg'].append(slate['summary']['gppAverage'])
			slates_dict['CashAvg'].append(slate['summary']['cashAverage'])
		else:
			slates_dict['GPPAvg'].append(0)
			slates_dict['CashAvg'].append(0)
	slates_df = pd.DataFrame.from_dict(slates_dict)
	slates_df.set_index('Id', inplace=True)
	slates_df.to_csv(ml_dir + '/slates/%s.csv' % date)
	print("Extract MoneyLine for %s" % date)

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--date", dest="date", default=datetime.today().astimezone(pytz.timezone('America/Los_Angeles')).strftime('%Y-%m-%d'))
	parser.add_option("-s", "--start_date", dest="start_date", default="")
	parser.add_option("-e", "--end_date", dest="end_date", default="")
	parser.add_option("-t", dest="crawler_type", default='RG')
	(options, args) = parser.parse_args()
	if options.crawler_type == 'RG':
		if options.start_date == "" or options.end_date == "":
			RGExtractor(options.date)
		else:
			for date in daterange(datetime.strptime(options.start_date, '%Y-%m-%d'), datetime.strptime(options.end_date, '%Y-%m-%d')):
				RGExtractor(date.strftime('%Y-%m-%d'))
	elif options.crawler_type == 'GameLog':
		GameLogExtractor('2018-19', 'Regular Season')
	elif options.crawler_type == 'ML':
		if options.start_date == "" or options.end_date == "":
			if options.date == datetime.today().strftime('%Y-%m-%d'):
				options.date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
			MoneyLineExtractor(options.date)
		else:
			for date in daterange(datetime.strptime(options.start_date, '%Y-%m-%d'), datetime.strptime(options.end_date, '%Y-%m-%d')):
				MoneyLineExtractor(date.strftime('%Y-%m-%d'))
	else:
		print("Extractor type %s not supported yet." % options.crawler_type)