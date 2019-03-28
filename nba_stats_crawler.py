from nba_api.stats.endpoints import commonallplayers
from nba_api.stats.endpoints import playergamelog
import time
import os

home = './'

def get_all_players_game_log(season, season_type):
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
		game_log.to_csv(game_log_dir + '/%s.csv' % player_name)
		time.sleep(1)


if __name__ == "__main__":
	get_all_players_game_log('2018-19', 'Regular Season')
