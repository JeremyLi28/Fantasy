import pandas as pd
import numpy as np
import os
import sys
from optparse import OptionParser
import datetime
from datetime import timedelta, date, datetime

home = './'

def daterange(start_date, end_date):
	for n in range(int ((end_date - start_date).days)):
		yield start_date + timedelta(n)

def RMSE(actual, expected, n):
    rmse_df = pow(expected - actual, 2)
    return np.sqrt(rmse_df.sum() / n) / actual.mean()

def MAE(actual, expected, n):
    mae_df = abs(expected - actual)
    return mae_df.sum() / n / actual.mean()

def TP(actual, expected):
    return expected.sum() / actual.sum()

def analysis():
    analysis_dir = home + 'data/analysis'
    results_dir = home + 'data/results'
    if not os.path.exists(analysis_dir):
        os.makedirs(analysis_dir)
    res_dict = {'Date' : [], 'RG_RMSE' : [], 'RG_MAE': [], 'RG_TP': [], 'SAVG_RMSE' : [], 'SAVG_MAE': [], 'SAVG_TP': []}
    for file_name in os.listdir(results_dir):
        date = os.path.splitext(file_name)[0]
        print date
        res = pd.read_csv(results_dir + '/' + file_name)
        n = len(res)
        res_dict['Date'].append(date)
        res_dict['RG_RMSE'].append(RMSE(res['DKP'], res['RGP'], n))
        res_dict['RG_MAE'].append(MAE(res['DKP'], res['RGP'], n))
        res_dict['RG_TP'].append(TP(res['DKP'], res['RGP']))
        res_dict['SAVG_RMSE'].append(RMSE(res['DKP'], res['SAVG'], n))
        res_dict['SAVG_MAE'].append(MAE(res['DKP'], res['SAVG'], n))
        res_dict['SAVG_TP'].append(TP(res['DKP'], res['SAVG']))
    res_df = pd.DataFrame.from_dict(res_dict)
    res_df.set_index('Date', inplace=True)
    res_df.sort_index(inplace=True)
    res_df.to_csv(analysis_dir + '/projection_results.csv')

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--date", dest="date", default=datetime.today().strftime('%Y-%m-%d'))
	parser.add_option("-s", "--start_date", dest="start_date", default="")
	parser.add_option("-e", "--end_date", dest="end_date", default="")
	(options, args) = parser.parse_args()
	analysis()
