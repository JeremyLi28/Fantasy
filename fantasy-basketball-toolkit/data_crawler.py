from bs4 import BeautifulSoup
import sys
import json
from optparse import OptionParser
import datetime
from datetime import timedelta, date, datetime
from nba_api.stats.endpoints import commonallplayers
from nba_api.stats.endpoints import playergamelog
import time
import os
from draft_kings.data import Sport
from draft_kings.client import contests, available_players
from utils import *
import pandas as pd
import urllib3
import pytz
import logging
from urllib.request import urlopen

home = '../'

def daterange(start_date, end_date):
	for n in range(int ((end_date - start_date).days)):
		yield start_date + timedelta(n)

def RGCrawler(date):
	url = 'https://rotogrinders.com/projected-stats/nba-player?site=draftkings&sport=nba&date=%s' % (date)
	opener = urllib3.build_opener()
	cookie = open(home + 'cookie.txt').read()
	opener.addheaders.append(('Cookie', cookie))
	r = opener.open(url).read()
	soup = BeautifulSoup(r, features="html.parser")
	# Have 2 scripts tag, we use the 2nd for now, the usage of first need to be further investigated, related to vegas money line
	script_tags = soup.find('section', {'class' : 'pag bdy'}).findAll('script')
	if len(script_tags) < 3:
		print ("Invalid date: %s" % date)
		return
	player_data = script_tags[2].text.split('\n')[2].strip().split('=')[1].strip()[:-1]
	slate_data = script_tags[1].text.split('\n')[4].strip().split('slates: ')[1][:-1]
	schedule_data = script_tags[1].text.split('\n')[5].strip().split('schedules: ')[1][:-1]
	player_json_data = json.loads(player_data)
	slate_json_data = json.loads(slate_data)
	with open(home + 'data/crawler/rotogrinders/slates/%s.json' % (date), 'w') as slate_json_file:
		json.dump(slate_json_data, slate_json_file)
	with open(home + 'data/crawler/rotogrinders/projections/%s.json' % (date), 'w') as player_json_file:
		json.dump(player_json_data, player_json_file)
	print ("Crawl RotoGrinders data for %s" % (date))

def GameLogCrawler(season, season_type):
	game_log_dir = home + 'data/crawler/nba_stats/player_game_log/%s' % season
	if not os.path.exists(game_log_dir):
		os.makedirs(game_log_dir)
	
	all_players_this_season = commonallplayers.CommonAllPlayers(is_only_current_season=1, league_id='00', season='2018-19').common_all_players.get_data_frame()
	
	for index, row in all_players_this_season[['PERSON_ID', 'DISPLAY_FIRST_LAST']].iterrows():
		player_id = row[0]
		player_name = row[1]
		print (player_name)
		game_log = playergamelog.PlayerGameLog(player_id=player_id, season_all='2018-19', season_type_all_star=season_type).get_data_frames()[0]
		double_count = game_log['PTS'].apply(lambda x: 1 if x >= 10 else 0) + game_log['REB'].apply(lambda x: 1 if x >= 10 else 0) + game_log['AST'].apply(lambda x: 1 if x >= 10 else 0) + game_log['STL'].apply(lambda x: 1 if x >= 10 else 0) + game_log['BLK'].apply(lambda x: 1 if x >= 10 else 0)
		game_log['DKP'] = game_log['PTS'] + 0.5 * game_log['FG3M'] + 1.25 * game_log['REB'] + 1.5 * game_log['AST'] + 2 * (game_log['STL'] + game_log['BLK']) - 0.5 * game_log['TOV'] + double_count.apply(lambda x : 1.5 if x >= 2 else 0) + double_count.apply(lambda x : 3 if x >= 3 else 0)
		game_log['GAME_DATE'] = game_log['GAME_DATE'].apply(lambda x: datetime.strptime(x, '%b %d, %Y').strftime('%Y-%m-%d'))
		game_log.to_csv(game_log_dir + '/%s.csv' % player_name)
		time.sleep(1)
	print ("Crawl NBA game log for %s %s" % (season, season_type))

def MoneyLineCrawler(date):
	ml_dir = GetMetaDataPath() + '/draftkings/moneyline'
	CreateDirectoryIfNotExist(ml_dir + '/contests/raw')
	CreateDirectoryIfNotExist(ml_dir + '/slates/raw')

	year, month, day = date.split('-')
	slates_url = "https://resultsdb-api.rotogrinders.com/api//slates?start=%s/%s/%s" % (month, day, year)
	r = urlopen(slates_url).read()
	slates = json.loads(r)
	nba_slates = []
	for slate in slates:
		if slate['sport'] == 3:
			summary_url = 'https://resultsdb-api.rotogrinders.com/api//slates/%s/summary' % slate['_id']
			summary = ""
			try:
				summary = json.loads(urlopen(summary_url).read())
			except ValueError as e:
				print ("No summary find %s" % slate['_id'])
			if summary != "":
				slate['summary'] = summary
			nba_slates.append(slate)
	contests_url = 'https://resultsdb-api.rotogrinders.com/api//contests?start=%s/%s/%s&lean=true' % (month, day, year)
	r = urlopen(contests_url).read()
	contests = json.loads(r)
	nba_contests = []
	for contest in contests:
		if contest['sport'] == 3:
			nba_contests.append(contest)
	with open(ml_dir + '/slates/raw/%s.json' % (date), 'w') as slate_json_file:
		json.dump(nba_slates, slate_json_file)
	with open(ml_dir + '/contests/raw/%s.json' % (date), 'w') as contest_json_file:
		json.dump(nba_contests, contest_json_file)
	print ("Crawl MoneyLine data for %s" % (date))

def DKCrawler():
	CreateDirectoryIfNotExist(GetMetaDataPath() + '/draftkings')
	dk_info = contests(sport=Sport.NBA)
	if not dk_info['contests']:
		print ("Contests Empty!")
	if not dk_info['groups']:
		print ("Slates Empty!")
	date = dk_info['groups'][0]['starts_at'].astimezone(pytz.timezone('America/Los_Angeles')).date()
	logging.info("======== DKCrawler for date %s ========" % date)
	for slate in dk_info['groups']:
		slate_date = slate['starts_at'].astimezone(pytz.timezone('America/Los_Angeles')).date()
		if slate_date < date:
			date = slate_date

	# Crawl contest information.
	CreateDirectoryIfNotExist(GetMetaDataPath() + '/draftkings/contests')
	contests_dict = {'CONTEST_ID': [], 'SLATE_ID' : [], 'NAME': [], 'START_TIMESTAMP': [], 'SPORT': [], 'FANTASY_PLAYER_POINTS': [], \
		'IS_GUARANTEED': [], 'IS_STARRED': [], 'IS_HEAD_TO_HEAD': [], 'IS_DOUBLE_UP': [], 'IS_FIFTY_FIFTY': [], 'TOTAL_ENTRIES': [], \
		'MAXIMUM_ENTRIES': [], 'ENTRY_FEE': [], 'TOTAL_PAYOUT': []}
	for contest in dk_info['contests']:
		if contest['sport'] is not Sport.NBA:
			continue
		contest_time = contest['starts_at'].astimezone(pytz.timezone('America/Los_Angeles'))
		if contest_time.date() != date:
			continue
		contests_dict['CONTEST_ID'].append(contest['id'])
		contests_dict['START_TIMESTAMP'].append(contest_time)
		contests_dict['FANTASY_PLAYER_POINTS'].append(contest['fantasy_player_points'])
		contests_dict['SPORT'].append(contest['sport'])
		contests_dict['NAME'].append(contest['name'])
		contests_dict['IS_GUARANTEED'].append(contest['guaranteed'])
		contests_dict['IS_STARRED'].append(contest['starred'])
		contests_dict['IS_HEAD_TO_HEAD'].append(contest['head_to_head'])
		contests_dict['IS_DOUBLE_UP'].append(contest['double_up'])
		contests_dict['IS_FIFTY_FIFTY'].append(contest['fifty_fifty'])
		contests_dict['TOTAL_ENTRIES'].append(contest['entries']['total'])
		contests_dict['MAXIMUM_ENTRIES'].append(contest['entries']['maximum'])
		contests_dict['ENTRY_FEE'].append(contest['entries']['fee'])
		contests_dict['TOTAL_PAYOUT'].append(contest['payout'])
		contests_dict['SLATE_ID'].append(contest['draft_group_id'])
	contests_df = pd.DataFrame.from_dict(contests_dict)
	contests_df.set_index('CONTEST_ID')
	contests_df.to_csv(GetMetaDataPath() + '/draftkings/contests/%s.csv' % date.strftime('%Y-%m-%d'))
	logging.info("Crawl DraftKings Contests for %s, # of contests: %d" % (date.strftime('%Y-%m-%d'), len(contests_df)))

	# Crawl slate information.
	CreateDirectoryIfNotExist(GetMetaDataPath() + '/draftkings/slates')
	slates_dict = {'SLATE_ID': [], 'SLATE_TYPE': [], 'START_TIMESTAMP': [], 'SPORT': [], 'GAMES_COUNT': []}
	for slate in dk_info['groups']:
		slate_time = slate['starts_at'].astimezone(pytz.timezone('America/Los_Angeles'))
		if slate_time.date() != date:
			continue
		slates_dict['SLATE_ID'].append(slate['id'])
		slates_dict['SLATE_TYPE'].append(DRAFTKINGS_SLATE_TYPE[slate['contest_type_id']])
		slates_dict['START_TIMESTAMP'].append(slate_time)
		slates_dict['SPORT'].append(slate['sport'])
		slates_dict['GAMES_COUNT'].append(slate['games_count'])
	slates_df = pd.DataFrame.from_dict(slates_dict)
	slates_df.set_index('SLATE_ID')
	slates_df.to_csv(GetMetaDataPath() + '/draftkings/slates/%s.csv' % date.strftime('%Y-%m-%d'))
	logging.info("Crawl DraftKings Slates for %s" % date.strftime('%Y-%m-%d'))
	print(slates_df)

	# Crawl player information
	CreateDirectoryIfNotExist(GetMetaDataPath() + '/draftkings/players')
	players_dict =  {'NAME': [], 'DK_ID': [], 'POSITION': [], 'SALARY': [], 'SLATE_ID': [], 'GAME_INFO': [], 'TEAM': [], 'DKP': []}
	for slate_id in slates_dict['SLATE_ID']:
		lines = urlopen(GetDKPlayersForSlateUrl(slate_id))

		# Header contains lineup position
		header = next(lines).decode("utf-8")
		start_column = 0
		end_column = header.index('Instructions') - 2
		lineup_positions = header[start_column:end_column].split(',')

		# Go through instruction lines
		while True:
			line = next(lines).decode("utf-8")
			if "Position" in line:
				start_column = line.index("Position")
				break

		# Parse players data
		for line in lines:
			# POST data is in bytes
			line = line.decode("utf-8")
			fields = line[start_column:].split(',')
			# For tier slate, set salary as 1
			if len(fields) == 8:
				fields.insert(5, 1)
			players_dict['NAME'].append(fields[2])
			players_dict['DK_ID'].append(fields[3])
			players_dict['POSITION'].append(fields[4])
			players_dict['SALARY'].append(fields[5])
			players_dict['SLATE_ID'].append(slate_id)
			players_dict['GAME_INFO'].append(fields[6])
			players_dict['TEAM'].append(fields[7])
			players_dict['DKP'].append(fields[8])
	players_df = pd.DataFrame.from_dict(players_dict)
	players_df.set_index('NAME')
	players_df.to_csv(GetMetaDataPath() + '/draftkings/players/%s.csv' % date.strftime('%Y-%m-%d'))
	logging.info("Crawl DraftKings Players for %s" % date.strftime('%Y-%m-%d'))


if __name__ == "__main__":
	CreateDirectoryIfNotExist(GetMetaDataPath())
	logging.basicConfig(filename='/tmp/data_crawler.log',
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)
	parser = OptionParser()
	parser.add_option("-d", "--date", dest="date", default=datetime.today().strftime('%Y-%m-%d'))
	parser.add_option("-s", "--start_date", dest="start_date", default="")
	parser.add_option("-e", "--end_date", dest="end_date", default="")
	parser.add_option("-t", dest="crawler_type", default='RG')
	(options, args) = parser.parse_args()
	if options.crawler_type == 'RG':
		if options.start_date == "" or options.end_date == "":
			RGCrawler(options.date)
		else:
			for date in daterange(datetime.strptime(options.start_date, '%Y-%m-%d'), datetime.strptime(options.end_date, '%Y-%m-%d')):
				RGCrawler(date.strftime('%Y-%m-%d'))
	elif options.crawler_type == 'GameLog':
		GameLogCrawler('2018-19', 'Regular Season')
	elif options.crawler_type == 'ML':
		if options.start_date == "" or options.end_date == "":
			MoneyLineCrawler(options.date)
		else:
			for date in daterange(datetime.strptime(options.start_date, '%Y-%m-%d'), datetime.strptime(options.end_date, '%Y-%m-%d')):
				MoneyLineCrawler(date.strftime('%Y-%m-%d'))
	elif options.crawler_type == 'DK':
		DKCrawler()
	else:
		print ("Crawler type %s not supported yet." % options.crawler_type)