from bs4 import BeautifulSoup
import urllib
import pandas as pd
import numpy as np
import os
import sys
import json

# RotoGrinders provides download for current day, and web page in the format of:
# https://rotogrinders.com/projected-stats/nba-player?site=draftkings&sport=nba&date=2018-11-10
# Current I manually download csv everyday, in the future, a script should be used to 
# automatically parse from url.
# The date is stored in the format of ./data/projections/rotogrinders/YYYY-MM-DD.csv 
def fetch_roto_grinders_projection(year, month, day):
	return pd.read_csv('./data/projections/rotogrinders/%s-%s-%s.csv' % (year, month, day), names=["Name", "DK Salary", "Team", "Position", "Opp", "Ceiling", "Floor", "Projection"])


# DK results data is parsed from rotoguru daily, in the format of 
# http://rotoguru1.com/cgi-bin/hyday.pl?mon=11&day=10&year=2018&game=dk&scsv=1
# results will be stored in 
def fetch_dk_result(year, month, day):
	path = './data/results/%s-%s-%s.csv' % (year, month, day)
	r = urllib.urlopen('http://rotoguru1.com/cgi-bin/hyday.pl?mon=%s&day=%s&year=%s&game=dk&scsv=1' % (month, day, year)).read()
	soup = BeautifulSoup(r, features="html.parser")
	raw = soup.find('pre').find('pre').text.split('\n')
	dk_res = []
	for line in raw:
		fields = line.split(';')
		if len(fields) == 14:
			dk_res.append(fields)
	dk_res_df = pd.DataFrame(dk_res[1:], columns=dk_res[0])
	dk_res_df['Name'] = dk_res_df['Name'].apply(lambda x: (x.split(',')[1] + ' ' + x.split(',')[0]).strip())
	dk_res_df['DK Pts'] = dk_res_df['DK Pts'].astype(float)
	dk_res_df.to_csv(path)
	return dk_res_df

def fetch_roto_ql_projection(year, month, day):
	path = './data/raw/rotoql-projection/%s-%s-%s.json' % (year, month, day)
	json_data = open(path).read()
	data = json.loads(json_data)
	proj_dict = {}
	names = []
	for player in data['playerEntryList']:
		names.append(player['firstName'] + ' ' + player['lastName'])
	proj_dict['Name'] = names;
	for i in range(4):
		title = data['playerProjectionTableList'][i]['title']
		words = title.split(' ')
		if i == 0:
			title = words[0]
		elif i == 1:
			title = ' '.join(words[0:2])
		projs = [] 
		for proj in data['playerProjectionTableList'][i]['playerProjectionList']:
			projs.append(proj['value'])
		proj_dict[title] = projs
	proj_df = pd.DataFrame.from_dict(proj_dict)
	proj_df = proj_df.set_index('Name')
	proj_df.to_csv('./data/projections/rotoql/%s-%s-%s.csv' % (year, month, day))
	return proj_df
	
def fetch_line_ups(year, month, day):
	path = './data/lineups/%s-%s-%s.csv' % (year, month, day)
	lineups = pd.read_csv(path, header=0)
	lineups_count = lineups[['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL']].stack().value_counts().to_frame(name='Count')
	lineups_count['Percent'] = lineups_count['Count'] / len(lineups)
	lineups_count.index.name = 'Name'
	lineups_count.index = lineups_count.index.map(lambda x : ' '.join(x.split()[:-1]))
	return lineups_count


def daily_report(year, month, day):
	dk_res_df = fetch_dk_result(year, month, day)
	rg_proj = fetch_roto_grinders_projection(year, month, day)
	ql_proj = fetch_roto_ql_projection(year, month, day)
	lineups = fetch_line_ups(year, month, day)
	join_res_rg = dk_res_df.set_index('Name').join(rg_proj.set_index('Name'), how='inner', on='Name', lsuffix='_res', rsuffix='_rg')[['Date', 'DK Pts', 'Projection', 'DK Salary_rg']].fillna(0)
	join_res_rg.columns = ['Date', 'DK Pts', 'RG Proj', 'DK Salary']
	join_res_rg = join_res_rg.join(ql_proj, how='inner', on='Name', lsuffix='_res', rsuffix='_rg').fillna(0)
	join_res_rg.columns = ['Date', 'DK Pts', 'RG Proj', 'DK Salary', 'GR Proj', '5AVG', 'RQ Proj', 'SAVG']
	join_res_rg['RG MAE'] = abs(join_res_rg['DK Pts'] - join_res_rg['RG Proj'])
	join_res_rg['RG RMSE'] = pow(join_res_rg['DK Pts'] - join_res_rg['RG Proj'], 2)
	join_res_rg['RG MAE Percent'] = join_res_rg['RG MAE'] / join_res_rg['DK Pts']
	join_res_rg['RQ MAE'] = abs(join_res_rg['DK Pts'] - join_res_rg['RQ Proj'])
	join_res_rg['RQ RMSE'] = pow(join_res_rg['DK Pts'] - join_res_rg['RQ Proj'], 2)
	join_res_rg['RQ MAE Percent'] = join_res_rg['RQ MAE'] / join_res_rg['DK Pts']
	join_res_rg['GR MAE'] = abs(join_res_rg['DK Pts'] - join_res_rg['GR Proj'])
	join_res_rg['GR RMSE'] = pow(join_res_rg['DK Pts'] - join_res_rg['GR Proj'], 2)
	join_res_rg['GR MAE Percent'] = join_res_rg['GR MAE'] / join_res_rg['DK Pts']
	join_res_rg['5AVG MAE'] = abs(join_res_rg['DK Pts'] - join_res_rg['5AVG'])
	join_res_rg['5AVG RMSE'] = pow(join_res_rg['DK Pts'] - join_res_rg['5AVG'], 2)
	join_res_rg['5AVG MAE Percent'] = join_res_rg['5AVG MAE'] / join_res_rg['DK Pts']
	join_res_rg['SAVG MAE'] = abs(join_res_rg['DK Pts'] - join_res_rg['SAVG'])
	join_res_rg['SAVG RMSE'] = pow(join_res_rg['DK Pts'] - join_res_rg['SAVG'], 2)
	join_res_rg['SAVG MAE Percent'] = join_res_rg['SAVG MAE'] / join_res_rg['DK Pts']
	join_res_rg['DK Pts/k'] = join_res_rg['DK Pts'] / join_res_rg['DK Salary'] * 1000
	lineups_stats = lineups.join(join_res_rg, how='inner', on='Name')
	print "===== Line ups ====="
	print lineups_stats[['Count', 'Percent', 'DK Salary', 'DK Pts', 'GR Proj', 'RQ Proj', '5AVG', 'SAVG', 'DK Pts/k']]
	print ""
	print "===== Summary ====="
	print "Best 10 player:"
	print join_res_rg.loc[join_res_rg['DK Salary'] != 0].sort_values(by=['DK Pts/k'], ascending=False)[['Date', 'DK Pts', 'RG Proj', 'DK Salary', 'GR Proj', '5AVG', 'RQ Proj', 'SAVG', 'DK Pts/k']].head(10)
	print ""
	print "Worst 10 player:"
	print join_res_rg.sort_values(by=['DK Pts/k', 'DK Salary'], ascending=[True, False])[['Date', 'DK Pts', 'RG Proj', 'DK Salary', 'GR Proj', '5AVG', 'RQ Proj', 'SAVG', 'DK Pts/k']].head(10)
	print ""
	print "===== RotoGrinders Projection ====="
	print "RG MAE: " + str(join_res_rg['RG MAE'].sum() / len(join_res_rg))
	print "RG RMSE: " + str(np.sqrt(join_res_rg['RG RMSE'].sum() / len(join_res_rg)))
	print "Res/Proj: " + str(join_res_rg['DK Pts'].sum() / join_res_rg['RG Proj'].sum())
	print "Weighted RG MAE: " + str((join_res_rg['RG MAE'] * join_res_rg['DK Salary']).sum() / join_res_rg['DK Salary'].sum())
	print "Weighted RG RMSE: " + str(np.sqrt((join_res_rg['RG RMSE'] * join_res_rg['DK Salary']).sum() / join_res_rg['DK Salary'].sum()))
	print "Weighted Res/Proj: " + str((join_res_rg['DK Pts'] * join_res_rg['DK Salary']).sum() / (join_res_rg['RG Proj'] * join_res_rg['DK Salary']).sum())
	print ""
	# print "Top 10 hit:"
	# print join_res_rg.loc[(join_res_rg['RG Proj'] != 0) | (join_res_rg['DK Pts'] != 0)].sort_values(by=['RG MAE Percent']).head(10)
	# print ""
	# print "Top 10 miss:"
	# print join_res_rg.sort_values(by=['RG MAE Percent'], ascending=False).head(10)
	print ""
	print "===== RotoQL Projection ====="
	print "RQ MAE: " + str(join_res_rg['RQ MAE'].sum() / len(join_res_rg))
	print "RQ RMSE: " + str(np.sqrt(join_res_rg['RQ RMSE'].sum() / len(join_res_rg)))
	print "Res/Proj: " + str(join_res_rg['DK Pts'].sum() / join_res_rg['RQ Proj'].sum())
	print "Weighted RQ MAE: " + str((join_res_rg['RQ MAE'] * join_res_rg['DK Salary']).sum() / join_res_rg['DK Salary'].sum())
	print "Weighted RQ RMSE: " + str(np.sqrt((join_res_rg['RQ RMSE'] * join_res_rg['DK Salary']).sum() / join_res_rg['DK Salary'].sum()))
	print "Weighted Res/Proj: " + str((join_res_rg['DK Pts'] * join_res_rg['DK Salary']).sum() / (join_res_rg['RQ Proj'] * join_res_rg['DK Salary']).sum())
	print ""
	# print "Top 10 hit:"
	# print join_res_rg.loc[(join_res_rg['RQ Proj'] != 0) | (join_res_rg['DK Pts'] != 0)].sort_values(by=['RQ MAE Percent']).head(10)
	# print ""
	# print "Top 10 miss:"
	# print join_res_rg.sort_values(by=['RQ MAE Percent'], ascending=False).head(10)
	print ""
	print "===== Data Guru Projection ====="
	print "GR MAE: " + str(join_res_rg['GR MAE'].sum() / len(join_res_rg))
	print "GR RMSE: " + str(np.sqrt(join_res_rg['GR RMSE'].sum() / len(join_res_rg)))
	print "Res/Proj: " + str(join_res_rg['DK Pts'].sum() / join_res_rg['GR Proj'].sum())
	print "Weighted GR MAE: " + str((join_res_rg['GR MAE'] * join_res_rg['DK Salary']).sum() / join_res_rg['DK Salary'].sum())
	print "Weighted GR RMSE: " + str(np.sqrt((join_res_rg['GR RMSE'] * join_res_rg['DK Salary']).sum() / join_res_rg['DK Salary'].sum()))
	print "Weighted Res/Proj: " + str((join_res_rg['DK Pts'] * join_res_rg['DK Salary']).sum() / (join_res_rg['GR Proj'] * join_res_rg['DK Salary']).sum())
	print ""
	# print "Top 10 hit:"
	# print join_res_rg.loc[(join_res_rg['GR Proj'] != 0) | (join_res_rg['DK Pts'] != 0)].sort_values(by=['GR MAE Percent']).head(10)
	# print ""
	# print "Top 10 miss:"
	# print join_res_rg.sort_values(by=['GR MAE Percent'], ascending=False).head(10)
	print ""
	print "===== Last 5 Game Average ====="
	print "5AVG MAE: " + str(join_res_rg['5AVG MAE'].sum() / len(join_res_rg))
	print "5AVG RMSE: " + str(np.sqrt(join_res_rg['5AVG RMSE'].sum() / len(join_res_rg)))
	print "Res/Proj: " + str(join_res_rg['DK Pts'].sum() / join_res_rg['5AVG'].sum())
	print "Weighted 5AVG MAE: " + str((join_res_rg['5AVG MAE'] * join_res_rg['DK Salary']).sum() / join_res_rg['DK Salary'].sum())
	print "Weighted 5AVG RMSE: " + str(np.sqrt((join_res_rg['5AVG RMSE'] * join_res_rg['DK Salary']).sum() / join_res_rg['DK Salary'].sum()))
	print "Weighted Res/Proj: " + str((join_res_rg['DK Pts'] * join_res_rg['DK Salary']).sum() / (join_res_rg['5AVG'] * join_res_rg['DK Salary']).sum())
	print ""
	# print "Top 10 hit:"
	# print join_res_rg.loc[(join_res_rg['5AVG'] != 0) | (join_res_rg['DK Pts'] != 0)].sort_values(by=['5AVG MAE Percent']).head(10)
	# print ""
	# print "Top 10 miss:"
	# print join_res_rg.sort_values(by=['5AVG MAE Percent'], ascending=False).head(10)
	print ""
	print "===== Season Average ====="
	print "SAVG MAE: " + str(join_res_rg['SAVG MAE'].sum() / len(join_res_rg))
	print "SAVG RMSE: " + str(np.sqrt(join_res_rg['SAVG RMSE'].sum() / len(join_res_rg)))
	print "Res/Proj: " + str(join_res_rg['DK Pts'].sum() / join_res_rg['SAVG'].sum())
	print "Weighted SAVG MAE: " + str((join_res_rg['SAVG MAE'] * join_res_rg['DK Salary']).sum() / join_res_rg['DK Salary'].sum())
	print "Weighted SAVG RMSE: " + str(np.sqrt((join_res_rg['SAVG RMSE'] * join_res_rg['DK Salary']).sum() / join_res_rg['DK Salary'].sum()))
	print "Weighted Res/Proj: " + str((join_res_rg['DK Pts'] * join_res_rg['DK Salary']).sum() / (join_res_rg['SAVG'] * join_res_rg['DK Salary']).sum())
	print ""
	# print "Top 10 hit:"
	# print join_res_rg.loc[(join_res_rg['SAVG'] != 0) | (join_res_rg['DK Pts'] != 0)].sort_values(by=['SAVG MAE Percent']).head(10)
	# print ""
	# print "Top 10 miss:"
	# print join_res_rg.sort_values(by=['SAVG MAE Percent'], ascending=False).head(10)

def main():
	pass


if __name__ == "__main__":
	year = sys.argv[1]
	month = sys.argv[2]
	day = sys.argv[3]
	daily_report(year, month, day)
