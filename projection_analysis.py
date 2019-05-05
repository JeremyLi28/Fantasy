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

def RMSE(expected, actual, n):
	rmse_df = pow(expected - actual, 2)
	return np.sqrt(rmse_df.sum() / n)

def MAE(expected, actual, n):
	mae_df = abs(expected - actual)
	return mae_df.sum() / n

def TP(expected, actual):
	return expected.sum() / actual.sum()

def analysis(proj_type, verbose):
	results_dir = home + 'data/results/daily'
	proj_dir = home + 'data/projections/%s' % proj_type
	res_dict = {'Date' : [], 'RMSE' : [], 'NRMSE' : [], 'MAE': [],  'NMAE': [], 'TP': [], 'COV' : []}
	for file_name in os.listdir(proj_dir):
		if file_name.startswith('.'):
			continue
		date = os.path.splitext(file_name)[0]
		if verbose:
		  print "Analysing results for %s " % date
		proj = pd.read_csv(proj_dir + '/' + file_name, header=0, index_col=0)
		if not os.path.exists(results_dir + '/%s.csv' % date):
			if verbose:
				print "No results for %s" % date
			continue		   
		res = pd.read_csv(results_dir + '/%s.csv' % date, header=0, index_col=0)
		proj_res = proj.join(res['DKP'], how="inner", on="name")
		if proj_res.empty:
			if verbose:
				print "No join results between projections and results for %s" % date
			continue
		n = len(proj_res)
		dkp_mean = proj_res['DKP'].mean()
		res_dict['Date'].append(date)
		res_dict['RMSE'].append(RMSE(proj_res['Proj'], proj_res['DKP'], n))
		res_dict['NRMSE'].append(RMSE(proj_res['Proj'], proj_res['DKP'], n) / dkp_mean)
		res_dict['MAE'].append(MAE(proj_res['Proj'], proj_res['DKP'], n))
		res_dict['NMAE'].append(MAE(proj_res['Proj'], proj_res['DKP'], n) / dkp_mean)
		res_dict['TP'].append(TP(proj_res['Proj'], proj_res['DKP']))
		res_dict['COV'].append(len(proj_res) * 1.0 / len(res))
	res_df = pd.DataFrame.from_dict(res_dict)
	res_df.set_index('Date', inplace=True)
	res_df.sort_index(inplace=True)
	analysis_dir = home + 'data/analysis'
	if not os.path.exists(analysis_dir):
		os.makedirs(analysis_dir)
	res_df.to_csv(analysis_dir + '/%s.csv' % proj_type)
	print "==== %s ======" % proj_type
	print res_df.mean()

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--date", dest="date", default=datetime.today().strftime('%Y-%m-%d'))
	parser.add_option("-s", "--start_date", dest="start_date", default="")
	parser.add_option("-e", "--end_date", dest="end_date", default="")
	parser.add_option("-t", "--type",  dest="proj_type", default="season_avg")
	parser.add_option("-v", "--verbose", dest="verbose", default=False)
	(options, args) = parser.parse_args()
	analysis(options.proj_type, options.verbose)
