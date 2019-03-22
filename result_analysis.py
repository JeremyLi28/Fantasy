from bs4 import BeautifulSoup
import urllib
import pandas as pd
import numpy as np
import os
import sys
import json

home = './'

# DK results data is parsed from rotoguru daily, in the format of
# http://rotoguru1.com/cgi-bin/hyday.pl?mon=11&day=10&year=2018&game=dk&scsv=1
# results will be stored in
def fetch_dk_result(year, month, day):
    path = home + 'data/results/%s-%s-%s.csv' % (year, month, day)
    r = urllib.urlopen(
        'http://rotoguru1.com/cgi-bin/hyday.pl?mon=%s&day=%s&year=%s&game=dk&scsv=1' % (month, day, year)).read()
    soup = BeautifulSoup(r, features="html.parser")
    pre_tags = soup.findAll('pre')
    raw = pre_tags[-1].text.split('\n')
    print raw
    dk_res = []
    for line in raw:
        fields = line.split(';')
        if len(fields) == 14:
            dk_res.append(fields)
	dk_res_df = pd.DataFrame(dk_res[1:], columns=dk_res[0])
    dk_res_df['Name'] = dk_res_df['Name'].apply(
        lambda x: (x.split(',')[1] + ' ' + x.split(',')[0]).strip())
    dk_res_df['DK Pts'] = dk_res_df['DK Pts'].astype(float)
    dk_res_df.to_csv(path)
    return dk_res_df


def fetch_rg_proj(year, month, day):
	proj_path = home + 'data/extractor/rotogrinders/projections/%s-%s-%s.csv' % (year, month, day)
	proj_data = pd.read_csv(proj_path, header = 0, index_col = 0)
	return proj_data

def calculate_rmse(year, month, day):
	res = fetch_dk_result(year, month, day)
	rg_proj = fetch_rg_proj(year, month, day)
	join_res_rg = res.set_index('Name').join(rg_proj.set_index('Name'), how='inner', on='Name', lsuffix='_res', rsuffix='_rg')[['Date', 'DK Pts', 'Projection', 'DK Salary_rg']].fillna(0)
	join_res_rg.columns = ['Date', 'DK Pts', 'RG Proj', 'DK Salary']
	join_res_rg['RG RMSE'] = pow(join_res_rg['DK Pts'] - join_res_rg['RG Proj'], 2)
	print "RG RMSE: " + str(np.sqrt(join_res_rg['RG RMSE'].sum() / len(join_res_rg)))
	print "Proj/Res: " + str(join_res_rg['RG Proj'].sum() / join_res_rg['DK Pts'].sum())

if __name__ == "__main__":
    year = sys.argv[1]
    month = sys.argv[2]
    day = sys.argv[3]
    calculate_rmse(year, month, day)