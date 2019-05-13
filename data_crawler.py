from bs4 import BeautifulSoup
import urllib
import sys
import json
from optparse import OptionParser
import datetime
from datetime import timedelta, date, datetime
from nba_api.stats.endpoints import commonallplayers
from nba_api.stats.endpoints import playergamelog
import time
import os
from draft_kings_client import DraftKingsClient, Sport
from utils import CreateDirectoryIfNotExist, GetRawDataPath, GetExtractedDataPath
import pandas as pd

home = './'

def daterange(start_date, end_date):
	for n in range(int ((end_date - start_date).days)):
		yield start_date + timedelta(n)

def RGCrawler(date):
	url = 'https://rotogrinders.com/projected-stats/nba-player?site=draftkings&sport=nba&date=%s' % (date)
	r = urllib.urlopen(url).read()
	soup = BeautifulSoup(r, features="html.parser")
	# Have 2 scripts tag, we use the 2nd for now, the usage of first need to be further investigated, related to vegas money line
	script_tags = soup.find('section', {'class' : 'pag bdy'}).findAll('script')
	if len(script_tags) < 3:
		print "Invalid date: %s" % date
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
	print "Crawl RotoGrinders data for %s" % (date)

def GameLogCrawler(season, season_type):
	game_log_dir = home + 'data/crawler/nba_stats/player_game_log/%s' % season
	if not os.path.exists(game_log_dir):
		os.makedirs(game_log_dir)
	
	all_players_this_season = commonallplayers.CommonAllPlayers(is_only_current_season=1, league_id='00', season='2018-19').common_all_players.get_data_frame()
	
	for index, row in all_players_this_season[['PERSON_ID', 'DISPLAY_FIRST_LAST']].iterrows():
		player_id = row[0]
		player_name = row[1]
		print player_name
		game_log = playergamelog.PlayerGameLog(player_id=player_id, season_all='2018-19', season_type_all_star=season_type).get_data_frames()[0]
		double_count = game_log['PTS'].apply(lambda x: 1 if x >= 10 else 0) + game_log['REB'].apply(lambda x: 1 if x >= 10 else 0) + game_log['AST'].apply(lambda x: 1 if x >= 10 else 0) + game_log['STL'].apply(lambda x: 1 if x >= 10 else 0) + game_log['BLK'].apply(lambda x: 1 if x >= 10 else 0)
		game_log['DKP'] = game_log['PTS'] + 0.5 * game_log['FG3M'] + 1.25 * game_log['REB'] + 1.5 * game_log['AST'] + 2 * (game_log['STL'] + game_log['BLK']) - 0.5 * game_log['TOV'] + double_count.apply(lambda x : 1.5 if x >= 2 else 0) + double_count.apply(lambda x : 3 if x >= 3 else 0)
		game_log['GAME_DATE'] = game_log['GAME_DATE'].apply(lambda x: datetime.strptime(x, '%b %d, %Y').strftime('%Y-%m-%d'))
		game_log.to_csv(game_log_dir + '/%s.csv' % player_name)
		time.sleep(1)
	print "Crawl NBA game log for %s %s" % (season, season_type)

def ResultCrawler(date):
	results_dir = home + 'data/crawler/results'
	if not os.path.exists(results_dir):
		os.makedirs(results_dir)
	if not os.path.exists(results_dir + '/slates'):
		os.makedirs(results_dir + '/slates')
	if not os.path.exists(results_dir + '/contests'):
		os.makedirs(results_dir + '/contests')
	year, month, day = date.split('-')
	slates_url = "https://resultsdb-api.rotogrinders.com/api//slates?start=%s/%s/%s" % (month, day, year)
	r = urllib.urlopen(slates_url).read()
	slates = json.loads(r)
	nba_slates = []
	for slate in slates:
		if slate['sport'] == 3:
			summary_url = 'https://resultsdb-api.rotogrinders.com/api//slates/%s/summary' % slate['_id']
			summary = ""
			try:
				summary = json.loads(urllib.urlopen(summary_url).read())
			except ValueError, e:
				print "No summary find %s" % slate['_id']
			if summary != "":
				slate['summary'] = summary
			nba_slates.append(slate)
	contests_url = 'https://resultsdb-api.rotogrinders.com/api//contests?start=%s/%s/%s&lean=true' % (month, day, year)
	r = urllib.urlopen(contests_url).read()
	contests = json.loads(r)
	nba_contests = []
	for contest in contests:
		if contest['sport'] == 3:
			nba_contests.append(contest)
	with open(results_dir + '/slates/%s.json' % (date), 'w') as slate_json_file:
		json.dump(nba_slates, slate_json_file)
	with open(results_dir + '/contests/%s.json' % (date), 'w') as contest_json_file:
		json.dump(nba_contests, contest_json_file)
	print "Crawl Result data for %s" % (date)

def DKCrawler():
	CreateDirectoryIfNotExist(GetExtractedDataPath() + '/draftkings')
	dk_info = DraftKingsClient.get_contests(sport=Sport.nba)
	if not dk_info.contests:
		print "Contests Empty!"
	if not dk_info.draft_groups:
		print "Slates Empty!"
	date = dk_info.contests[0].start_timestamp.strftime('%Y-%m-%d')
	CreateDirectoryIfNotExist(GetExtractedDataPath() + '/draftkings/contests')
	contests_dict = {'CONTEST_ID': [], 'SLATE_ID' : [], 'NAME': [], 'START_TIMESTAMP': [], 'SPORT': [], 'FANTASY_PLAYER_POINTS': [], \
		'IS_GUARANTEED': [], 'IS_STARRED': [], 'IS_HEAD_TO_HEAD': [], 'IS_DOUBLE_UP': [], 'IS_FIFTY_FIFTY': [], 'TOTAL_ENTRIES': [], \
		'MAXIMUM_ENTRIES': [], 'ENTRY_FEE': [], 'TOTAL_PAYOUT': []}
	for contest in dk_info.contests:
		if contest.sport is not Sport.nba:
			continue
	   	contests_dict['CONTEST_ID'].append(contest.contest_id)
		contests_dict['START_TIMESTAMP'].append(contest.start_timestamp)
		contests_dict['FANTASY_PLAYER_POINTS'].append(contest.fantasy_player_points)
		contests_dict['SPORT'].append(contest.sport)
		contests_dict['NAME'].append(contest.name)
		contests_dict['IS_GUARANTEED'].append(contest.is_guaranteed)
		contests_dict['IS_STARRED'].append(contest.is_starred)
		contests_dict['IS_HEAD_TO_HEAD'].append(contest.is_head_to_head)
		contests_dict['IS_DOUBLE_UP'].append(contest.is_double_up)
		contests_dict['IS_FIFTY_FIFTY'].append(contest.is_fifty_fifty)
		contests_dict['TOTAL_ENTRIES'].append(contest.total_entries)
		contests_dict['MAXIMUM_ENTRIES'].append(contest.maximum_entries)
		contests_dict['ENTRY_FEE'].append(contest.entry_fee)
		contests_dict['TOTAL_PAYOUT'].append(contest.total_payout)
		contests_dict['SLATE_ID'].append(contest.draft_group_id)
	contests_df = pd.DataFrame.from_dict(contests_dict)
	contests_df.set_index('CONTEST_ID')
	contests_df.to_csv(GetExtractedDataPath() + '/draftkings/contests/%s.csv' % date)
	print "Crawl DraftKings Contests for %s" % date


if __name__ == "__main__":
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
	elif options.crawler_type == 'Result':
		if options.start_date == "" or options.end_date == "":
			ResultCrawler(options.date)
		else:
			for date in daterange(datetime.strptime(options.start_date, '%Y-%m-%d'), datetime.strptime(options.end_date, '%Y-%m-%d')):
				ResultCrawler(date.strftime('%Y-%m-%d'))
	elif options.crawler_type == 'DK':
		DKCrawler()
	else:
		print "Crawler type %s not supported yet." % options.crawler_type