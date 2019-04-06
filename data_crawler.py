from bs4 import BeautifulSoup
import urllib
import sys
import json
from optparse import OptionParser
import datetime
from nba_api.stats.endpoints import commonallplayers
from nba_api.stats.endpoints import playergamelog
import time
import os

home = './'

def CrawlRG(date):
	url = 'https://rotogrinders.com/projected-stats/nba-player?site=draftkings&sport=nba&date=%s' % (date)
	r = urllib.urlopen(url).read()
	soup = BeautifulSoup(r, features="html.parser")
	# Have 2 scripts tag, we use the 2nd for now, the usage of first need to be further investigated, related to vegas money line
	script_tags = soup.find('section', {'class' : 'pag bdy'}).findAll('script')
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

def CrawlGameLog(season, season_type):
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
		game_log['GAME_DATE'] = game_log['GAME_DATE'].apply(lambda x: datetime.datetime.strptime(x, '%b %d, %Y').strftime('%Y-%m-%d'))
		game_log.to_csv(game_log_dir + '/%s.csv' % player_name)
		time.sleep(1)
	print "Crawl NBA game log for %s %s" % (season, season_type)


if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--date", dest="date", default=datetime.datetime.today().strftime('%Y-%m-%d'))
	parser.add_option("--gl", action="store_true", dest="crawl_game_log", default=False)
	parser.add_option("--rg", action="store_true", dest="crawl_rg", default=False)
	(options, args) = parser.parse_args()
	if options.crawl_rg:
		CrawlRG(options.date)
	if options.crawl_game_log:
		CrawlGameLog('2018-19', 'Regular Season')